#!/usr/bin/env python3
import sys
import os
from copy import deepcopy
import time

import CommonModule as CM
import ConcurrentModule as ConM


######################################################
################### Primitive tasks ##################
######################################################

def o_PT1_precond(state, agent):
    return state.var1.val > 0
def o_PT1_effects(state, agent):
    state.var1.val += 2
o_PT1 = CM.Operator("PT1", pre_cond=o_PT1_precond, effects=o_PT1_effects)

def o_PT2_precond(state, agent):
    return state.var1.val > 0
def o_PT2_effects(state, agent):
    state.var1.val += 1
o_PT2 = CM.Operator("PT2", pre_cond=o_PT2_precond, effects=o_PT2_effects)

def o_PT3_precond(state, agent):
    return state.var1.val > 0
o_PT3 = CM.Operator("PT3", pre_cond=o_PT3_precond)

def ro_PT4_donecond(state, agent):
    return True
ro_PR4 = CM.Operator("PT4", done_cond=ro_PT4_donecond)

def ho_PT4_effects(state, agent):
    state.var1.val += 5
ho_PT4 = CM.Operator("PT4", effects=ho_PT4_effects)

## pick ##
def o_pick_precond(state, agent, o):
    if o=="o1":
        return state.pos_o1.val=="table"
    if o=="o2":
        return state.pos_o2.val=="table"
def o_pick_effects(state, agent, o):
    if o=="o1":
        state.pos_o1.val=agent
    if o=="o2":
        state.pos_o2.val=agent
o_pick = CM.Operator("pick", pre_cond=o_pick_precond, effects=o_pick_effects)

common_ops = [o_PT1, o_PT2, o_PT3, o_pick]
robot_ops = common_ops + [ro_PR4]
human_ops = common_ops + [ho_PT4]


######################################################
################### Abstract Tasks ###################
######################################################

### AT1 ###
def m_AT1_r1_pre_cond(state, agent):
    return True
def m_AT1_r1_decomp(state, agent):
    return [("PT1",)]
m_AT1_r1 = CM.Method("AT1", pre_cond=m_AT1_r1_pre_cond, decomp=m_AT1_r1_decomp)

def m_AT1_r2_decomp(state, agent):
    return [("PT2",)]
m_AT1_r2 = CM.Method("AT1", decomp=m_AT1_r2_decomp)

def m_AT1_h1_decomp(state, agent):
    return [("PT4",)]
m_AT1_h1 = CM.Method("AT1", decomp=m_AT1_h1_decomp)

### AT2 ###
m_AT2 = CM.Method("AT2")

## Pickup ##
def m_Pickup_o1_precond(state, agent):
    return state.pos_o1.val=="table"
def m_Pickup_o1_decomp(state, agent):
    return [("pick", "o1")]
m_Pickup_o1 = CM.Method("Pickup", pre_cond=m_Pickup_o1_precond, decomp=m_Pickup_o1_decomp)

def m_Pickup_o2_precond(state, agent):
    return state.pos_o2.val=="table"
def m_Pickup_o2_decomp(state, agent):
    return [("pick", "o2")]
m_Pickup_o2 = CM.Method("Pickup", pre_cond=m_Pickup_o2_precond, decomp=m_Pickup_o2_decomp)

common_methods = [("AT2",m_AT2), ("Pickup",m_Pickup_o1,m_Pickup_o2)]
robot_methods = common_methods + [("AT1",m_AT1_r1,m_AT1_r2)]
human_methods = common_methods + [("AT1",m_AT1_h1)]


######################################################
###################### Triggers ######################
######################################################

common_triggers = []
robot_triggers = common_triggers + []
human_triggers = common_triggers + []


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

    # Dynamic properties
    initial_state.create_dyn_fluent("pos_o1", "table") # table, agent, end_pos_1/2 
    initial_state.create_dyn_fluent("pos_o2", "table")

    # Robot init #
    CM.declare_operators(robot_name, robot_ops)
    CM.declare_methods(robot_name, robot_methods)
    # htpa.declare_triggers(robot_name, *robot_triggers)
    robot_state = deepcopy(initial_state)
    robot_state.__name__ = robot_name + "_init"
    robot_state.self_name.val = robot_name
    CM.set_state(robot_name, robot_state)
    CM.add_tasks(robot_name, [("Pickup",)])

    # Human init #
    CM.declare_operators(human_name, human_ops)
    CM.declare_methods(human_name, human_methods)
    human_state = deepcopy(initial_state)
    human_state.__name__ = human_name + "_init"
    human_state.self_name.val = human_name
    CM.set_state(human_name, human_state)
    CM.add_tasks(human_name, [("Pickup",)])

    # Starting Agent
    CM.set_starting_agent(robot_name)

if __name__ == "__main__":
    initDomain()
    sol = ConM.explore()
    ConM.show_solution(sol)
    ConM.dumping_solution(sol)