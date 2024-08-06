#!/usr/bin/env python3
import sys
import os
from copy import deepcopy
import time
from pympler import asizeof
from enum import Enum


import CommonModule as CM
import ConcurrentModule as ConM
import solution_checker

import cProfile
import pstats

######################################################
################### Primitive tasks ##################
######################################################


## turnOn1 ##
def o_turnOn1pre(state, agent):
    return state.switch1=='off'
def o_turnOn1_effects(state, agent):
    state.switch1 = 'on'
o_turnOn1 = CM.Operator("turnOn1", pre_cond=o_turnOn1pre, effects=o_turnOn1_effects)

## turnOn2 ##
def o_turnOn2pre(state, agent):
    return state.switch2=='off'
def o_turnOn2_effects(state, agent):
    state.switch2 = 'on'
o_turnOn2 = CM.Operator("turnOn2", pre_cond=o_turnOn2pre, effects=o_turnOn2_effects)

## turnOff1 ##
def o_turnOff1pre(state, agent):
    return state.switch1=='on'
def o_turnOff1_effects(state, agent):
    state.switch1 = 'off'
o_turnOff1 = CM.Operator("turnOff1", pre_cond=o_turnOff1pre, effects=o_turnOff1_effects)

## turnOff2 ##
def o_turnOff2pre(state, agent):
    return state.switch2=='on'
def o_turnOff2_effects(state, agent):
    state.switch2 = 'off'
o_turnOff2 = CM.Operator("turnOff2", pre_cond=o_turnOff2pre, effects=o_turnOff2_effects)

## break1 ##
def o_break1_effects(state, agent):
    state.switch1 = 'broken'
o_break1 = CM.Operator('break1', effects=o_break1_effects)

## break2 ##
def o_break2_effects(state, agent):
    state.switch2 = 'broken'
o_break2 = CM.Operator('break2', effects=o_break2_effects)

common_ops = [o_turnOn1, o_turnOn2, o_turnOff1, o_turnOff2, o_break1, o_break2]
robot_ops = common_ops + []
human_ops = common_ops + []


######################################################
################### Abstract Tasks ###################
######################################################

## Task ##
def m_Task_done(state, agent):
    return state.switch1=='on' and state.switch2=='on'
def m_Task_multi_decomp(state, agent):
    multi_subtasks = []

    multi_subtasks.append([ ('turnOn1',), ('Task',) ])
    multi_subtasks.append([ ('turnOn2',), ('Task',) ])
    multi_subtasks.append([ ('turnOff1',), ('Task',) ])
    multi_subtasks.append([ ('turnOff2',), ('Task',) ])
    multi_subtasks.append([ ('break1',), ('Task',) ])
    multi_subtasks.append([ ('break2',), ('Task',) ])

    if multi_subtasks==[]:
        raise Exception("problem..")
    return multi_subtasks
m_Task = CM.Method('Task', multi_decomp=m_Task_multi_decomp, done_cond=m_Task_done)


common_methods = [m_Task]
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
    return state.switch1=='on' and state.switch2=='on'    

def is_robot(agent):
    return agent=="R"

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

    new_init_state = CM.InitState()
    new_init_state.create_dyn_fluent('holding', {'R':None, 'H':None})

    new_init_state.create_dyn_fluent('switch1', 'off')
    new_init_state.create_dyn_fluent('switch2', 'off')
    
    CM.set_initial_state(new_init_state)

    # Robot init #
    CM.declare_R_operators(robot_ops)
    CM.declare_R_methods(robot_methods)
    CM.set_initial_R_agenda([("Task",)])

    # Human init #
    CM.declare_H_operators(human_ops)
    CM.declare_H_methods(human_methods)
    CM.set_initial_H_agenda([  ])

def main():
    sys.setrecursionlimit(100000)
    initDomain()

    s_t = time.time()
    ConM.explore()
    print("time to explore: %.2fs" %(time.time()-s_t))

    solution_checker.new_check_solution(goal_condition)
    print(f"Back edges: ", CM.g_BACK_EDGES)
    print(f"Number of leaves: {len(CM.g_FINAL_IPSTATES)}")
    print(f"Nb states before pruning = {len(CM.g_PSTATES)}")
    ConM.prune_deadends()
    print(f"Nb states after pruning = {len(CM.g_PSTATES)}")

    ConM.dumping_solution()

if __name__ == "__main__":
    main()
