import stack_empiler_2
import sys
import ConcurrentModule as ConM
import CommonModule as CM
import time

import solution_checker

import choice_updater
from choice_updater import exec_chrono
import numpy as np


def scenario_1():

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

def scenario_2():
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
        # 'l6',
        # 'l7',
        # 'l8',
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
            # self.l6_color = 'w'
            # self.l6_on = {'l4'}
            # self.l7_color = 'b'
            # self.l7_on = {'l5'}
            # self.l8_color = 'p'
            # self.l8_on = {'l6','l7'}

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

def scenario_3():
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
        # 'l7',
        # 'l8',
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
            # self.l7_color = 'b'
            # self.l7_on = {'l5'}
            # self.l8_color = 'p'
            # self.l8_on = {'l6','l7'}

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

def scenario_4():

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
        # 'l8',
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
            # self.l8_color = 'p'
            # self.l8_on = {'l6','l7'}

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

def scenario_5():
    CUBES = {
        'b1',
        'g1',
        's1',
        'p2',
        'r1',
        'b3',
        'y1',
        'w1',
        'o1',
        'b2',
        'p1',
        'r2',
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
            self.b3_on = {'C'}

            self.b2_on = {'H'}
            self.p1_on = {'H'}
            self.r2_on = {'H'}

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
        'l9',
        'l10',
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
            self.l9_color = 'b'
            self.l9_on = {'table'}
            self.l10_color = 'r'
            self.l10_on = {'l9'}
            self.l5_color = 's'
            self.l5_on = {'l3','l10'}
            self.l7_color = 'b'
            self.l7_on = {'l5'}
            self.l4_color = 'o'
            self.l4_on = {'l3'}
            self.l6_color = 'w'
            self.l6_on = {'l4'}
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

def scenario_6():
    CUBES = {
        'b1',
        'g1',
        's1',
        'p2',
        'r1',
        'b3',
        'y1',
        'w1',
        'o1',
        'b2',
        'p1',
        'r2',
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
            self.b3_on = {'C'}

            self.b2_on = {'H'}
            self.p1_on = {'H'}
            self.r2_on = {'H'}

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
        # 'l6',
        # 'l7',
        # 'l8',
        'l9',
        'l10',
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
            self.l5_on = {'l3','l10'}
            # self.l6_color = 'w'
            # self.l6_on = {'l4'}
            # self.l7_color = 'b'
            # self.l7_on = {'l5'}
            # self.l8_color = 'p'
            # self.l8_on = {'l6','l7'}
            self.l9_color = 'b'
            self.l9_on = {'table'}
            self.l10_color = 'r'
            self.l10_on = {'l9'}

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

def scenario_7():
    CUBES = {
        'b1',
        'g1',
        's1',
        'p2',
        'r1',
        'b3',
        'y1',
        'w1',
        'o1',
        'b2',
        'p1',
        'r2',
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
            self.b3_on = {'C'}

            self.b2_on = {'H'}
            self.p1_on = {'H'}
            self.r2_on = {'H'}

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
        # 'l5',
        # 'l6',
        # 'l7',
        # 'l8',
        'l9',
        'l10',
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
            # self.l5_color = 's'
            # self.l5_on = {'l3','l10'}
            # self.l6_color = 'w'
            # self.l6_on = {'l4'}
            # self.l7_color = 'b'
            # self.l7_on = {'l5'}
            # self.l8_color = 'p'
            # self.l8_on = {'l6','l7'}
            self.l9_color = 'b'
            self.l9_on = {'table'}
            self.l10_color = 'r'
            self.l10_on = {'l9'}

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

def scenario_8():
    CUBES = {
        'b1',
        'g1',
        's1',
        'p2',
        'r1',
        'b3',
        'y1',
        'w1',
        'o1',
        'b2',
        'p1',
        'r2',
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
            self.b3_on = {'C'}

            self.b2_on = {'H'}
            self.p1_on = {'H'}
            self.r2_on = {'H'}

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
        # 'l4',
        # 'l5',
        # 'l6',
        # 'l7',
        # 'l8',
        'l9',
        'l10',
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
            # self.l4_color = 'o'
            # self.l4_on = {'l3'}
            # self.l5_color = 's'
            # self.l5_on = {'l3','l10'}
            # self.l6_color = 'w'
            # self.l6_on = {'l4'}
            # self.l7_color = 'b'
            # self.l7_on = {'l5'}
            # self.l8_color = 'p'
            # self.l8_on = {'l6','l7'}
            self.l9_color = 'b'
            self.l9_on = {'table'}
            self.l10_color = 'r'
            self.l10_on = {'l9'}

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


if __name__ == "__main__":
    sys.setrecursionlimit(100000)

    stack_empiler_2.initDomain()

    s_t = time.time()
    ConM.explore()
    print("time to explore: %.5fs" %(time.time()-s_t))

    if not solution_checker.new_check_solution(stack_empiler_2.goal_condition):
        exit()

    ConM.setPolicyName('task_end_early')
    exec_chrono(choice_updater.update_robot_policy, f"Computing robot policy {ConM.G_POLICY_NAME}")

    if len(sys.argv)>1 and sys.argv[1]=="1":
        print("\t Nb leaves = ", len(CM.g_FINAL_IPSTATES))
        print("\t Nb states = ", len(CM.g_PSTATES))

        exec_chrono(choice_updater.compute_traces, "Computing traces")
        lengths = np.array(choice_updater.g_lengths)

        print("\t Nb traces = ", len(lengths))
        print(f"\t Mean length = {np.mean(lengths):0.3f}")
        print(f"\t SD length = {np.std(lengths):.3f}")
        print("\t Min length = ", np.min(lengths))
        print("\t Max length = ", np.max(lengths))

        print("\t Best_metrics: ", choice_updater.str_print_metrics_priority(CM.g_PSTATES[0].best_metrics))
