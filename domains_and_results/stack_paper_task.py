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
    if agent=="H" and not pick_from in ["H","C"]:
        return False
    if agent=="R" and not pick_from in ["R","C"]:
        return False
    if state.color_cubes[color][pick_from]==0:
        return False
    return True
def o_pick_effects(state, agent, color, pick_from):
    state.color_cubes[color][pick_from] -= 1
    state.holding[agent] = color
o_pick = CM.Operator("pick", pre_cond=o_pick_precond, effects=o_pick_effects)

## place ##
def o_place_precond(state, agent, color, place_to):
    return state.holding[agent]==color and target_supports_ok(state, place_to) and target_free(state, place_to)
def o_place_effects(state, agent, color, place_to):
    state.locations[place_to] = color
    state.holding[agent] = None
o_place = CM.Operator("place", pre_cond=o_place_precond, effects=o_place_effects)

## drop ##
def o_drop_precond(state, agent, color):
    return state.holding[agent]==color
def o_drop_effects(state, agent, color):
    agent_side = "R" if agent=="R" else "H"
    state.color_cubes[color][agent_side] += 1
    state.holding[agent] = None
o_drop = CM.Operator("drop", pre_cond=o_drop_precond, effects=o_drop_effects)

## push ##
def o_push_effects(state, agent):
    state.locations["l3"] = state.holding[agent]
    state.holding[agent] = None
o_push = CM.Operator("push", effects=o_push_effects)

## open_box ##
def o_open_box_effects(state, agent, color):
    state.color_cubes[color]["R"] += state.color_cubes[color]["RB"]
    state.color_cubes[color]["RB"] = 0 
o_open_box = CM.Operator("open_box", effects=o_open_box_effects)


common_ops = [o_pick, o_place, o_drop]
robot_ops = common_ops + [o_push, o_open_box]
human_ops = common_ops + []


######################################################
################### Abstract Tasks ###################
######################################################

##################
# W   B   l4  l5 #
# --P--   --l3-- #
# R   Y   l1  l2 #
##################


## StackBis ##
def m_StackBis_precond(state, agent):
    for color in state.color_cubes:
        for side in state.color_cubes[color]:
            if state.color_cubes[color][side]>0 and can_be_placed(state, color):
                if agent=="R":
                    if side in ["R", "C", "RB"]:
                        return True
                elif agent=="H":
                    if side in ["H", "C"]:
                        return True
    return False    
def m_StackBis_donecond(state, agent):
    return goal_reached(state)
def m_StackBis_multi_decomp(state, agent):
    multi_subtasks = []

    for color in state.color_cubes:
        for side in state.color_cubes[color]:
            if state.color_cubes[color][side]>0 and can_be_placed(state, color):
                if agent=="R":
                    if side in ["R", "C"]:
                        multi_subtasks.append([ ("pick", color, side), ("PlaceBis", color), ("StackBis",) ])
                    elif side=="RB":
                        multi_subtasks.append([ ("open_box", color), ("StackBis",) ])
                elif agent=="H":
                    if side in ["H", "C"]:
                        multi_subtasks.append([ ("pick", color, side), ("PlaceBis", color), ("StackBis",) ])

    if multi_subtasks==[]:
        raise Exception("WeirdStack")
        multi_subtasks=[[]] # Done
    return multi_subtasks
m_StackBis = CM.Method("StackBis", pre_cond=m_StackBis_precond, done_cond=m_StackBis_donecond, multi_decomp=m_StackBis_multi_decomp)

## PlaceBis ##
def m_PlaceBis_precond(state, agent, color):
    return state.holding[agent]==color
def m_PlaceBis_multi_decomp(state, agent, color):
    multi_subtasks = []

    # Check if can place in stack, if so find and return corresponding PT, else drop the cube back on table
    if can_be_placed(state, color):
        for l in state.solution:
            if color in state.solution[l]["color"] and target_supports_ok(state, l) and target_free(state, l):
                multi_subtasks.append([ ("place", color, l) ])
    else:
        multi_subtasks.append([ ("drop", color) ])

    if multi_subtasks==[]:
        raise Exception("WeirdPlace")
    return multi_subtasks
m_PlaceBis = CM.Method("PlaceBis", pre_cond=m_PlaceBis_precond, multi_decomp=m_PlaceBis_multi_decomp)


common_methods = [m_StackBis, m_PlaceBis]
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

def goal_reached(state):
    # If agents are not holding a cube
    if state.holding["H"]!=None or state.holding["R"]!=None:
        return False
    
    # And if each location has the correct color placed
    goal_reached = True
    for l in state.locations:
        if not state.locations[l] in state.solution[l]["color"]:
            goal_reached = False
            break
    
    return goal_reached

def target_supports_ok(state, loc):
    on_locs = state.solution[loc]["on"]
    if on_locs[0]=="table":
        return True
    else:
        for on_loc in on_locs:
            if state.locations[on_loc]==None:
                return False
        return True

def target_free(state, loc):
    return state.locations[loc]==None

def can_be_placed(state, color):
    for l in state.solution:
        if color in state.solution[l]["color"] and target_supports_ok(state, l) and target_free(state, l):
            return True
    return False

######################################################
################## Goal Condition ####################
######################################################

def goal_condition(state):
    return goal_reached(state)


######################################################
######################## MAIN ########################
######################################################

def initDomain():
    # Set domain name
    domain_name = os.path.basename(__file__)[:-3] # filename minus ".py"
    CM.set_domain_name(domain_name)

    # Initial state
    initial_state = CM.State("init")

    # Static properties
    initial_state.create_static_fluent("self_name", "None")
    initial_state.create_static_fluent("solution", {
        "l1" : {"color":["r"], "on":["table"]},
        "l2" : {"color":["y"], "on":["table"]},
        "l3" : {"color":["p"], "on":["l1","l2"]},
        "l4" : {"color":["w"], "on":["l3"]},
        "l5" : {"color":["b"], "on":["l3"]},
        # "l4" : {"color":["w", "b"], "on":["l3"]},
        # "l5" : {"color":["b", "w"], "on":["l3"]},
    })

    # Dynamic properties
    initial_state.create_dyn_fluent("color_cubes", {
        "r": {"R":1, "RB":0, "C":0, "H":1},
        "y": {"R":0, "RB":0, "C":1, "H":0},
        "p": {"R":0, "RB":0, "C":0, "H":1},
        "b": {"R":0, "RB":1, "C":0, "H":1},
        "w": {"R":1, "RB":0, "C":0, "H":0},
    })
    initial_state.create_dyn_fluent("locations", {})
    for l in initial_state.solution:
        initial_state.locations[l] = None
    initial_state.create_dyn_fluent("holding", {"R":None, "H":None})
    CM.set_state(initial_state)

    # Robot init #
    CM.declare_operators("R", robot_ops)
    CM.declare_methods("R", robot_methods)
    CM.add_tasks("R", [("StackBis",)])

    # Human init #
    CM.declare_operators("H", human_ops)
    CM.declare_methods("H", human_methods)
    CM.add_tasks("H", [("StackBis",)])

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