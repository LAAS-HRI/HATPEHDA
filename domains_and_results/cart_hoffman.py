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

## move ##
def o_move_pre(state, agent, location):
    return state.loc[agent] != location
def o_move_effects(state, agent, location):
    state.loc[agent] = location
o_move = CM.Operator("move", pre_cond=o_move_pre, effects=o_move_effects)

## pickUp ##
def o_pickUp_pre(state, agent, obj):
    if state.holding[agent] == None:
        if state.loc[agent] == obj:
            return True
    return False
def o_pickUp_effects(state, agent, obj):
    state.holding[agent] = obj
o_pickUp = CM.Operator("pickUp", pre_cond=o_pickUp_pre, effects=o_pickUp_effects)

## putDownPart ##
def o_putDownPart_pre(state, agent):
    if already_two_comp(state):
        return False
    if state.loc[agent]!="workbench":
        return False
    if state.holding[agent]==None:
        return False
    return True
def o_putDownPart_effects(state, agent):
    if len(state.parts_bench)==0: # First part
        state.cart[state.holding[agent]].attached = True
    state.parts_bench = state.parts_bench.union({state.holding[agent]})
    state.holding[agent] = None
o_putDownPart = CM.Operator('putDownPart', pre_cond=o_putDownPart_pre, effects=o_putDownPart_effects)

## putDownTool ##
def o_putDownTool_effects(state, agent):
    state.holding[agent] = None
o_putDownTool = CM.Operator('putDownTool', effects=o_putDownTool_effects)

## UseTool ##
def o_useTool_pre(state, agent):
    if state.loc[agent]!="workbench":
        return False
    if state.holding[agent]=="rivet":
        if "axel1" in state.parts_bench and "floor" in state.parts_bench and not state.link_axel1_floor:
            return True
        elif "axel2" in state.parts_bench and "floor" in state.parts_bench and not state.link_axel2_floor:
            return True
    if state.holding[agent]=="welder":
        if "body" in state.parts_bench and "floor" in state.parts_bench and not state.link_body_floor:
            return True
    if state.holding[agent]=='wrench1':
        if "wheel1" in state.parts_bench and "axel1" in state.parts_bench and not state.link_wheel1_axel1:
            return True
        elif "wheel2" in state.parts_bench and "axel1" in state.parts_bench and not state.link_wheel2_axel1:
            return True
    if state.holding[agent]=='wrench2':
        if "wheel3" in state.parts_bench and "axel2" in state.parts_bench and not state.link_wheel3_axel2:
            return True
        elif "wheel4" in state.parts_bench and "axel2" in state.parts_bench and not state.link_wheel4_axel2:
            return True
    return False
def o_useTool_effects(state, agent):
    if state.holding[agent]=="rivet":
        if "axel1" in state.parts_bench and "floor" in state.parts_bench and not state.link_axel1_floor:
            state.link_axel1_floor = True
            state.cart['axel1'].attached = True
            state.cart['floor'].attached = True
        elif "axel2" in state.parts_bench and "floor" in state.parts_bench and not state.link_axel2_floor:
            state.link_axel2_floor = True
            state.cart['axel2'].attached = True
            state.cart['floor'].attached = True
    if state.holding[agent]=="welder":
        if "body" in state.parts_bench and "floor" in state.parts_bench and not state.link_body_floor:
            state.link_body_floor = True
            state.cart['body'].attached = True
            state.cart['floor'].attached = True
    if state.holding[agent]=='wrench1':
        if "wheel1" in state.parts_bench and "axel1" in state.parts_bench and not state.link_wheel1_axel1:
            state.link_wheel1_axel1 = True
            state.cart['wheel1'].attached = True
            state.cart['axel1'].attached = True
        elif "wheel2" in state.parts_bench and "axel1" in state.parts_bench and not state.link_wheel2_axel1:
            state.link_wheel2_axel1 = True
            state.cart['wheel2'].attached = True
            state.cart['axel1'].attached = True
    if state.holding[agent]=='wrench2':
        if "wheel3" in state.parts_bench and "axel2" in state.parts_bench and not state.link_wheel3_axel2:
            state.link_wheel3_axel2 = True
            state.cart['wheel3'].attached = True
            state.cart['axel2'].attached = True
        elif "wheel4" in state.parts_bench and "axel2" in state.parts_bench and not state.link_wheel4_axel2:
            state.link_wheel4_axel2 = True
            state.cart['wheel4'].attached = True
            state.cart['axel2'].attached = True
o_useTool = CM.Operator('useTool', effects=o_useTool_effects, pre_cond=o_useTool_pre)


common_ops = [o_move, o_pickUp]
robot_ops = common_ops + [o_putDownTool, o_useTool]
human_ops = common_ops + [o_putDownPart]


######################################################
################### Abstract Tasks ###################
######################################################

## Build ##
def m_Build_H_pre(state, agent):
    if already_two_comp(state):
        parts = get_connections(state)
        for p in state.parts_bench:
            if p in parts:
                parts.remove(p)
        if parts==[]:
            return False
    return True
def m_Build_H_done(state, agent):
    if state.holding[agent]==None:
        if  state.link_body_floor\
        and state.link_axel1_floor\
        and state.link_axel2_floor\
        and state.link_wheel1_axel1\
        and state.link_wheel2_axel1\
        and state.link_wheel3_axel2\
        and state.link_wheel4_axel2:
            return True
    return False
def m_Build_H_multi_decomp(state, agent):
    multi_subtasks = []

    # Identify remains parts to bring to workbench

    if len(state.parts_bench)==0:
        parts = ['body', 'floor', 'axel1', 'axel2', 'wheel1', 'wheel2', 'wheel3', 'wheel4']
    else:
        parts = get_connections(state)
    for p in state.parts_bench:
        if p in parts:
            parts.remove(p)

    # PickUp and PutDown Part
    for part in parts:
        if part not in state.parts_bench:
            multi_subtasks.append([ ('move', part), ('pickUp', part), ('move', 'workbench'), ('putDownPart',), ('Build',) ])

    if multi_subtasks==[]:
        raise Exception("problem..")
    return multi_subtasks
m_Build_H = CM.Method('Build', pre_cond=m_Build_H_pre, multi_decomp=m_Build_H_multi_decomp, done_cond=m_Build_H_done)

def m_Build_R_pre(state, agent):
    # if already_two_comp(state):
    #     parts = get_connections(state)
    #     for p in state.parts_bench:
    #         if p in parts:
    #             parts.remove(p)
    #     if parts==[]:
    #         return False
        
    if state.holding[agent]==None and identify_required_tools(state)==[]:
        return False
    return True
def m_Build_R_done(state, agent):
    if state.holding[agent]==None:
        if  state.link_body_floor\
        and state.link_axel1_floor\
        and state.link_axel2_floor\
        and state.link_wheel1_axel1\
        and state.link_wheel2_axel1\
        and state.link_wheel3_axel2\
        and state.link_wheel4_axel2:
            return True
    return False
def m_Build_R_multi_decomp(state, agent):
    multi_subtasks = []

    if state.holding[agent]==None:
        tools = identify_required_tools(state)
        for tool in tools:
            multi_subtasks.append([ ('move', tool), ('pickUp', tool), ('move', 'workbench'), ('Build',) ])
    else:
        multi_subtasks.append([ ('useTool',), ('move', state.holding[agent]), ('putDownTool',), ('Build',) ])
        multi_subtasks.append([ ('useTool',), ('useTool',), ('move', state.holding[agent]), ('putDownTool',), ('Build',) ])

    if multi_subtasks==[]:
        raise Exception("problem..")
    return multi_subtasks
m_Build_R = CM.Method('Build', pre_cond=m_Build_R_pre, multi_decomp=m_Build_R_multi_decomp, done_cond=m_Build_R_done)


common_methods = []
robot_methods = common_methods + [m_Build_R]
human_methods = common_methods + [m_Build_H]

######################################################
###################### Triggers ######################
######################################################

common_triggers = []
robot_triggers = common_triggers + []
human_triggers = common_triggers + []


######################################################
###################### Helpers #######################
######################################################


def identify_required_tools(state):

    connections = get_connections(state)

    tools = []

    if state.loc['H']!='workbench':
        part = state.loc['H']
        if part in connections:
            if part=='body':
                tools = ['welder']
            
            if part=='floor':
                if 'body' in state.parts_bench:
                    tools = ['welder']
                if 'axel1' in state.parts_bench:
                    tools = ['rivet']
                if 'axel2' in state.parts_bench:
                    tools = ['rivet']
            
            if part=='axel1':
                if 'floor' in state.parts_bench:
                    tools = ['rivet']
                if 'wheel1' in state.parts_bench:
                    tools = ['wrench1']
                if 'wheel2' in state.parts_bench:
                    tools = ['wrench1']
            
            if part=='axel2':
                if 'floor' in state.parts_bench:
                    tools = ['rivet']
                if 'wheel3' in state.parts_bench:
                    tools = ['wrench2']
                if 'wheel4' in state.parts_bench:
                    tools = ['wrench2']
            
            if part=='wheel1':
                tools = ['wrench1']
            
            if part=='wheel2':
                tools = ['wrench1']
            
            if part=='wheel3':
                tools = ['wrench2']
            
            if part=='wheel4':
                tools = ['wrench2']

    # if 'body' in connections:
    #     if not 'welder' in tools:
    #         tools.append('welder')
    # if 'floor' in connections:
    #     if not 'welder' in tools:
    #         tools.append('welder')
    #     if not 'rivet' in tools:
    #         tools.append('rivet')
    # if 'axel1' in connections:
    #     if not 'wrench1' in tools:
    #         tools.append('wrench1')
    #     if not 'rivet' in tools:
    #         tools.append('rivet')
    # if 'axel2' in connections:
    #     if not 'wrench2' in tools:
    #         tools.append('wrench2')
    #     if not 'rivet' in tools:
    #         tools.append('rivet')
    # if 'wheel1' in connections:
    #     if not 'wrench1' in tools:
    #         tools.append('wrench1')
    # if 'wheel2' in connections:
    #     if not 'wrench1' in tools:
    #         tools.append('wrench1')
    # if 'wheel3' in connections:
    #     if not 'wrench2' in tools:
    #         tools.append('wrench2')
    # elif 'wheel4' in connections:
    #     if not 'wrench2' in tools:
    #         tools.append('wrench2')

    return tools

def already_two_comp(state):
    if len(state.parts_bench)<2:
        return False

    objects = state.parts_bench
    n = 0
    if "body" in objects:
        n+=1
    if "floor" in objects:
        n+=1
    if "axel1" in objects:
        n+=1
    if "axel2" in objects:
        n+=1
    if "wheel1" in objects:
        n+=1
    if "wheel2" in objects:
        n+=1
    if "wheel3" in objects:
        n+=1
    if "wheel4" in objects:
        n+=1

    if state.link_body_floor:
        n-=1
    if state.link_axel1_floor:
        n-=1
    if state.link_axel2_floor:
        n-=1
    if state.link_wheel1_axel1:
        n-=1
    if state.link_wheel2_axel1:
        n-=1
    if state.link_wheel3_axel2:
        n-=1
    if state.link_wheel4_axel2:
        n-=1

    return n==2

def goal_reached(state):
    if state.holding['H']==None and state.holding['R']==None:
        if  state.link_body_floor\
        and state.link_axel1_floor\
        and state.link_axel2_floor\
        and state.link_wheel1_axel1\
        and state.link_wheel2_axel1\
        and state.link_wheel3_axel2\
        and state.link_wheel4_axel2:
            return True
    return False    

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

def get_connections(state):
    parts_to_connect = [p for p in state.cart]

    for p in state.cart.values():
        keep = False
        if not p.attached:
            for c in p.connections:
                if state.cart[c].attached:
                    keep = True
                    break
        if not keep:
            parts_to_connect.remove(p.name)

    return parts_to_connect

class Part:
    def __init__(self, name, connections) -> None:
        self.name = name
        self.attached = False
        self.connections = connections

    def __eq__(self, other: object) -> bool:
        return self.name==other.name and self.attached==other.attached and self.connections==other.connections

def initDomain():
    # Set domain name
    domain_name = os.path.basename(__file__)[:-3] # filename minus ".py"
    CM.set_domain_name(domain_name)

    new_init_state = CM.InitState()
    new_init_state.create_dyn_fluent('loc', {'R':'workbench', 'H':'workbench'}) 
    new_init_state.create_dyn_fluent('holding', {'R':None, 'H':None})

    new_init_state.create_dyn_fluent('parts_bench', set())
    
    new_init_state.create_dyn_fluent('cart', {})
    new_init_state.cart['body'] = Part('body', ['floor'])
    new_init_state.cart['floor'] = Part('floor', ['body', 'axel1', 'axel2'])
    new_init_state.cart['axel1'] = Part('axel1', ['floor', 'wheel1', 'wheel2'])
    new_init_state.cart['axel2'] = Part('axel2', ['floor', 'wheel3', 'wheel4'])
    new_init_state.cart['wheel1'] = Part('wheel1', ['axel1'])
    new_init_state.cart['wheel2'] = Part('wheel2', ['axel1'])
    new_init_state.cart['wheel3'] = Part('wheel3', ['axel2'])
    new_init_state.cart['wheel4'] = Part('wheel4', ['axel2'])

    new_init_state.create_dyn_fluent('link_body_floor', False)
    new_init_state.create_dyn_fluent('link_axel1_floor', False)
    new_init_state.create_dyn_fluent('link_axel2_floor', False)
    new_init_state.create_dyn_fluent('link_wheel1_axel1', False)
    new_init_state.create_dyn_fluent('link_wheel2_axel1', False)
    new_init_state.create_dyn_fluent('link_wheel3_axel2', False)
    new_init_state.create_dyn_fluent('link_wheel4_axel2', False)

    CM.set_initial_state(new_init_state)

    # Robot init #
    CM.declare_R_operators(robot_ops)
    CM.declare_R_methods(robot_methods)
    CM.set_initial_R_agenda([("Build",)])

    # Human init #
    CM.declare_H_operators(human_ops)
    CM.declare_H_methods(human_methods)
    CM.set_initial_H_agenda([("Build",)])

    # CM.set_starting_agent("H")

def main():
    sys.setrecursionlimit(100000)
    initDomain()
    # pr = cProfile.Profile()
    # pr.enable()

    s_t = time.time()
    ConM.explore()
    print("time to explore: %.2fs" %(time.time()-s_t))
    solution_checker.new_check_solution(goal_condition)
    print(f"Number of leaves: {len(CM.g_FINAL_IPSTATES)}")
    print(f"Nb states before pruning = {len(CM.g_PSTATES)}")
    ConM.prune_deadends()
    print(f"Nb states after pruning = {len(CM.g_PSTATES)}")
    
    # pr.disable()
    # stats = pstats.Stats(pr).sort_stats("tottime")
    # stats.dump_stats(filename="profiling.prof")


if __name__ == "__main__":

    tt_explore = False
    if len(sys.argv)>1 and sys.argv[1]=="tt":
        tt_explore = True
    
    main()

    ConM.dumping_solution()