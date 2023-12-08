#!/usr/bin/env python3
import sys
import os
from copy import deepcopy
import time
from pympler import asizeof


import CommonModule as CM
import ConcurrentModule as ConM
import solution_checker

import cProfile
import pstats

######################################################
################### Primitive tasks ##################
######################################################

## pick ##
# Picks a cube from a side
def o_pick_precond(state, agent, cube_name):
    return  cube_reachable_by(state, cube_name, agent)
def o_pick_effects(state, agent, cube_name):
    state.cubes.set_on(cube_name, set())
    state.cubes.computeBelow()
    state.holding.set(agent, cube_name)
o_pick = CM.Operator("pick", pre_cond=o_pick_precond, effects=o_pick_effects)

## place ##
# Places the cube held in the stack
def o_place_precond(state, agent, place_to, cube_name):
    return state.holding.get(agent)==cube_name and state.colors.get(cube_name)==state.solution.get_color(place_to) and target_supports_ok(state, place_to) and target_free(state, place_to)
def o_place_effects(state, agent, place_to, cube_name):
    state.stack.set(place_to, cube_name)
    state.holding.set(agent, None)
o_place = CM.Operator("place", pre_cond=o_place_precond, effects=o_place_effects)

## drop ##
# Places the cube held back in a side
def o_drop_precond(state, agent, cube_name, side):
    if state.holding.get(agent)==cube_name:
        if is_robot(agent):
            return side in {"R", "C"}
        else:
            return side in {"H", "C"}
    return False
def o_drop_effects(state, agent, cube_name, side):
    state.cubes.set_on(cube_name, {side})
    state.cubes.computeBelow()
    state.holding.set(agent, None)
o_drop = CM.Operator("drop", pre_cond=o_drop_precond, effects=o_drop_effects)

common_ops = [o_pick, o_place, o_drop]
robot_ops = common_ops + []
human_ops = common_ops + []


######################################################
################### Abstract Tasks ###################
######################################################

## Stack ##
def m_Stack_donecond(state, agent):
    return goal_reached(state)
def m_Stack_precond(state, agent):
    for cube in CUBES:
        if cube_side_reachable_by(state, cube, agent) and cube_can_be_placed(state, cube):
            return True
    return False    
def m_Stack_multi_decomp(state, agent):
    multi_subtasks = []

    for cube_name in CUBES:
        if cube_side_reachable_by(state, cube_name, agent) and cube_can_be_placed(state, cube_name):
            if cube_reachable_by(state, cube_name, agent):
                multi_subtasks.append([ ("pick", cube_name), ("Place", cube_name), ("Stack",) ])
            else: # Unstack
                multi_subtasks.append([ ("Unstack", cube_name), ("Stack",) ])

    if multi_subtasks==[]:
        raise Exception("WeirdStack")
        multi_subtasks=[[]] # Done
    return multi_subtasks
m_Stack = CM.Method("Stack", pre_cond=m_Stack_precond, done_cond=m_Stack_donecond, multi_decomp=m_Stack_multi_decomp)

## Unstack
def m_Unstack_decomp(state, agent, cube_name):
    cube_to_unstack = cube_name

    while state.cubes.get_below(cube_to_unstack)!=None:
        cube_to_unstack = state.cubes.get_below(cube_to_unstack)

    return [("pick", cube_to_unstack), ("Place", cube_to_unstack)]
m_Unstack = CM.Method("Unstack", decomp=m_Unstack_decomp)

## Place ##
# Tries to place the cube in the stack, otherwise drop it on the table
def m_Place_precond(state, agent, cube_name):
    return state.holding.get(agent)==cube_name
def m_Place_multi_decomp(state, agent, cube_name):
    multi_subtasks = []

    # Check if can place in stack, if so find and return corresponding PT, else drop the cube back on table
    if cube_can_be_placed(state, cube_name):
        for l in LOCATIONS:
            if state.colors.get(cube_name)==state.solution.get_color(l) and target_supports_ok(state, l) and target_free(state, l):
                multi_subtasks.append([ ("place", l, cube_name) ])
    else:
        multi_subtasks.append([ ("Drop", cube_name) ])

    if multi_subtasks==[]:
        raise Exception("WeirdPlace")
    return multi_subtasks
m_Place = CM.Method("Place", pre_cond=m_Place_precond, multi_decomp=m_Place_multi_decomp)

## Drop ##
# Tries to drop the cube in the center, otherwise on own side
# For now always drop in the center
def m_Drop_multi_decomp(state, agent, cube_name):
    multi_subtasks = []

    # multi_subtasks.append([ ("drop", cube_name, "C") ])

    if cube_name=='g1':
        multi_subtasks.append([ ("drop", cube_name, 'R') ])
    else:
        # TODO generalize
        for o in CM.g_PSTATES[0].state.cubes.get_on(cube_name): break
        multi_subtasks.append([ ("drop", cube_name, o) ])

    return multi_subtasks
m_Drop = CM.Method("Drop", multi_decomp=m_Drop_multi_decomp)

common_methods = [m_Stack, m_Place, m_Unstack, m_Drop]
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
    if state.holding.get('H')!=None or state.holding.get('R')!=None:
        return False
    
    # And if each location has the correct color placed
    for l in LOCATIONS:
        cube_placed_at_l = state.stack.get(l)
        if cube_placed_at_l==None:
            return False
        else:
            color_of_cube_placed_at_l = state.colors.get(cube_placed_at_l)
            color_that_should_be_at_l = state.solution.get_color(l)
            if color_of_cube_placed_at_l != color_that_should_be_at_l:
                return False
    return True    

def target_supports_ok(state, loc):
    on_locs = state.solution.get_on(loc)
    if on_locs=={'table'}:
        return True
    else:
        for on_loc in on_locs:
            if state.stack.get(on_loc)==None:
                return False
        return True

def target_free(state, loc):
    return state.stack.get(loc)==None

def cube_side_reachable_by(state, cube, agent):
    ons = state.cubes.get_on(cube)

    if ons == set(): # Means that cube is being held or is already placed
        return False
    
    for on in ons: break
    while not on in {'R', 'C', 'H'}:
        ons = state.cubes.get_on(on)
        for on in ons: break

    if is_robot(agent):
        return on in ["R", "C"]
    else:
        return on in ["H", "C"]
    
def cube_reachable_by(state, cube, agent):
    # if cube is in a side reachable by the agent
    # and if cube has no cubes on top of it
    return cube_side_reachable_by(state, cube, agent) and state.cubes.get_below(cube)==None

def cube_can_be_placed(state, cube):
    for l in LOCATIONS:
        if state.colors.get(cube)==state.solution.get_color(l) and target_supports_ok(state, l) and target_free(state, l):
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

CUBES = {
    'p2',
    'o1',
    'b1',
    'g1',
    'r1',
    's1',
    'y1',
    'w1',
    'b2',
    'p1',
}
class Cubes:

    __slots__ = ()
    for c in CUBES:
        __slots__ += (''.join((c, '_on')), ''.join((c, '_below')) )

    def __init__(self) -> None:
        self.p2_on = {'R'}
        self.b1_on = {'R'}
        self.g1_on = {'b1'}
        self.r1_on = {'R'}
        self.s1_on = {'R'}

        self.y1_on = {'C'}
        self.o1_on = {'C'}
        self.w1_on = {'C'}

        self.b2_on = {'H'}
        self.p1_on = {'H'}

        self.computeBelow()

    def computeBelow(self):
        for c in CUBES:
            setattr(self, ''.join([c, '_below']), None)
        for c in CUBES:
            c_on = getattr(self, ''.join([c, '_on']))
            if len(c_on):
                for cube_on in c_on: break
                if cube_on not in {'R', 'C', 'H'}:
                    setattr(self, ''.join([cube_on, '_below']), c)

    def get_on(self, cube_name):
        return getattr(self, ''.join([cube_name, '_on']))
    def set_on(self, cube_name, value):
        setattr(self, ''.join([cube_name, '_on']), value)
    
    def get_below(self, cube_name):
        return getattr(self, ''.join([cube_name, '_below']))
class Colors:

    __slots__ = CUBES
    
    def __init__(self) -> None:
        for c in CUBES:
            setattr(self, c, c[0])

    def get(self, cube_name):
        return getattr(self, cube_name)

LOCATIONS = {
    'l1',
    'l2',
    'l3',
    'l4',
    'l5',
    'l6',
    'l7',
    'l8',
}
class Solution:
    __slots__ = ()
    for l in LOCATIONS:
        __slots__ += ( ''.join((l, '_color')), ''.join((l, '_on')) )

    def __init__(self) -> None:
        self.l1_color = 'r'
        self.l1_on = {'table'}
        self.l2_color = 'y'
        self.l2_on = {'table'}
        self.l3_color = 'p'
        self.l3_on = {'l1','l2'}
        self.l4_color = 'o'
        self.l4_on = {'l3'}
        self.l5_color = 's'
        self.l5_on = {'l3'}
        self.l6_color = 'w'
        self.l6_on = {'l4'}
        self.l7_color = 'b'
        self.l7_on = {'l5'}
        self.l8_color = 'p'
        self.l8_on = {'l6','l7'}

    def get_on(self, l):
        return getattr(self, ''.join([l, '_on']))
    def get_color(self, l):
        return getattr(self, ''.join([l, '_color']))
class CurrentStack:

    __slots__ = LOCATIONS

    def __init__(self) -> None:
        for l in LOCATIONS:
            setattr(self, l, None)

    def get(self, l):
        return getattr(self, l)
    def set(self, l, value):
        setattr(self, l, value)

class Holding:
    __slots__ = ('R', 'H')
    def __init__(self) -> None:
        self.R = None
        self.H = None

    def get(self, agent_name):
        return getattr(self, agent_name)
    def set(self, agent_name, value):
        setattr(self, agent_name, value)

########################################################################################

def initDomain():
    # Set domain name
    domain_name = os.path.basename(__file__)[:-3] # filename minus ".py"
    CM.set_domain_name(domain_name)

    new_init_state = CM.InitState()
    new_init_state.create_static_fluent('solution', Solution())
    new_init_state.create_static_fluent('colors', Colors())
    new_init_state.create_dyn_fluent('cubes', Cubes())
    new_init_state.cubes.computeBelow()
    new_init_state.create_dyn_fluent('stack', CurrentStack())
    new_init_state.create_dyn_fluent('holding', Holding())
    CM.set_initial_state(new_init_state)

    # Robot init #
    CM.declare_R_operators(robot_ops)
    CM.declare_R_methods(robot_methods)
    CM.set_initial_R_agenda([("Stack",)])

    # Human init #
    CM.declare_H_operators(human_ops)
    CM.declare_H_methods(human_methods)
    CM.set_initial_H_agenda([("Stack",)])

    CM.set_starting_agent("H")

def main():
    sys.setrecursionlimit(100000)
    initDomain()
    # pr = cProfile.Profile()
    # pr.enable()

    s_t = time.time()
    ConM.explore()
    print("time to explore: %.2fs" %(time.time()-s_t))
    print(f"Number of leaves: {len(CM.g_FINAL_IPSTATES)}")
    print(f"Nb states = {len(CM.g_PSTATES)}")
    
    # pr.disable()
    # stats = pstats.Stats(pr).sort_stats("tottime")
    # stats.dump_stats(filename="profiling.prof")


if __name__ == "__main__":

    tt_explore = False
    if len(sys.argv)>1 and sys.argv[1]=="tt":
        tt_explore = True
    
    main()

    # solution_checker.check_solution(sol, goal_condition)

    # ConM.simplify_solution(sol)

    ConM.dumping_solution()