import stack_empiler_2
import sys
import ConcurrentModule as ConM
import CommonModule as CM
import time

import choice_updater
from choice_updater import exec_chrono
import numpy as np


CUBES = set()
LOCATIONS = set()

CubesClass = None
ColorsClass = None
SolutionClass = None
CurrentStackClass = None
HoldingClass = None

def scenario_1():
    global CUBES, LOCATIONS
    global CubesClass, ColorsClass, SolutionClass, CurrentStackClass, HoldingClass

    ###########################################

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

    ###########################################

    CubesClass = Cubes
    ColorsClass = Colors
    SolutionClass = Solution
    CurrentStackClass = CurrentStack
    HoldingClass = Holding

def initDomain():
    # Set domain name
    new_init_state = CM.InitState()
    new_init_state.create_static_fluent('solution', SolutionClass())
    new_init_state.create_static_fluent('colors', ColorsClass())
    new_init_state.create_dyn_fluent('cubes', CubesClass())
    new_init_state.cubes.computeBelow()
    new_init_state.create_dyn_fluent('stack', CurrentStackClass())
    new_init_state.create_dyn_fluent('holding', HoldingClass())
    CM.set_initial_state(new_init_state)

    # Robot init #
    CM.declare_R_operators(stack_empiler_2.robot_ops)
    CM.declare_R_methods(stack_empiler_2.robot_methods)
    CM.set_initial_R_agenda([("Stack",)])

    # Human init #
    CM.declare_H_operators(stack_empiler_2.human_ops)
    CM.declare_H_methods(stack_empiler_2.human_methods)
    CM.set_initial_H_agenda([("Stack",)])

if __name__ == "__main__":
    sys.setrecursionlimit(100000)

    scenario_1()

    initDomain()

    s_t = time.time()
    ConM.explore()
    print("time to explore: %.2fs" %(time.time()-s_t))

    exec_chrono(choice_updater.compute_traces, "Computing traces")
    lengths = np.array(choice_updater.g_lengths)

    print("\t Nb leaves = ", len(CM.g_FINAL_IPSTATES))
    print("\t Nb states = ", len(CM.g_PSTATES))
    print("\t Nb traces = ", len(lengths))
    print(f"\t Mean length = {np.mean(lengths):0.3f}")
    print(f"\t SD length = {np.std(lengths):.3f}")
    print("\t Min length = ", np.min(lengths))
    print("\t Max length = ", np.max(lengths))