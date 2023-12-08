#!/usr/bin/env python3

import hatpehda

from hatpehda.standard_domains import generate_standard_domain

import rospy
from std_msgs.msg import String

from ontologenius import OntologiesManipulator, OntologyManipulator

from typing import Dict

from functools import partial, update_wrapper
from itertools import permutations
from copy import deepcopy

from hatpehda.reg import REGHandler

from hatpehda.ros import RosNode

from hatpehda import gui

import time

"""
This example depicts the simple director task.

Result:
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB')] with cost: 16.0
Plan : [('robot_tell_human_to_tidy', 'human', 'cube_BGTB'), ('human_pick_cube', 'cube_BGTB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGTB'), ('robot_tell_human_to_tidy', 'human', 'cube_GGCB'), ('human_pick_cube', 'cube_GGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_BGCB'), ('human_pick_cube', 'cube_BGCB'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_BGCB'), ('robot_tell_human_to_tidy', 'human', 'cube_GBTG'), ('human_pick_cube', 'cube_GBTG'), ('human_drop_cube',), ('robot_wait_for_human_to_tidy', 'human', 'cube_GBTG')] with cost: 16.0
"""

### Helpers

regHandler = None


def same_last_tasks(plan, n, task=None):
    if len(plan) < n:
        return False
    last_tasks = [plan[-i].name for i in range(1, n + 1)]
    print("Last tasks:", last_tasks)
    if task is not None and last_tasks[0] != task:
        return False
    return last_tasks.count(last_tasks[0]) == len(last_tasks)


def get_box_containing_cube(state, cube):
    box = None
    if cube in state.isInContainer and state.isInContainer[cube] != []:
        for container in state.isInContainer[cube]:
            hatpehda.print_state(state)
            if container in state.individuals["DtBox"]:
                box = container
                break
    return box


def get_agent_role(state, name):
    if name in state.individuals["DtDirector"]:
        return "DtDirector"
    elif name in state.individuals["DtReceiver"]:
        return "DtReceiver"
    return None


def is_cube_pickable_by(state, name, cube):
    box = get_box_containing_cube(state, cube)
    if box is None:
        # The cube is not in a box, so let's say it is not reachable
        return False

    role = get_agent_role(state, name)
    if role is None:
        # The agent is not part of the DT, they cannot pick a cube
        return False

    if role == "DtDirector":
        return box in state.individuals["DirectorReachableDtBox"]
    if role == "DtReceiver":
        return box in state.individuals["ReceiverReachableDtBox"]
    return False


### Core

def retrieve_state_from_ontology(agent_name, state):
    ontos = OntologiesManipulator()
    ontos.waitInit()
    ontos.add(agent_name)
    onto = ontos.get(agent_name)
    # onto = OntologyManipulator()
    onto.close()
    for t, rels in state.types.items():
        indivs = onto.individuals.getType(t)
        if not hasattr(state, "individuals"):
            state.individuals = {}
        state.individuals[t] = indivs
        for rel in rels:
            if not hasattr(state, rel):
                setattr(state, rel, {})
            for indiv in indivs:
                related = onto.individuals.getOn(indiv, rel)
                getattr(state, rel)[indiv] = related
    hatpehda.print_state(state)
    return state


### Actions

def robot_tell_human_to_tidy(agents, self_state, self_name, human, cube, box):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @param human:
    @param cube:
    @return:
    @semantic_name: ask_to_put_pickable_in_container
    @ontology_type human: Human
    @ontology_type cube: Cube
    @ontology_type box: Box
    """
    if human in self_state.isReachableBy[cube]:
        ctx = [("?0", "isAbove", "table_1")]
        symbols = {"?0": cube}
        reg = regHandler.get_re(human, agents[human].state, ctx, symbols, cube)
        if not reg.success:
           return False
        cost = len(reg.sparqlResult)
        cost = 1
        print("Cube", cube, "costs", cost, "to disambiguate")
        hatpehda.add_tasks(human, [("tidy", cube, box)], agents)
        return agents
    else:
        print("cube", cube, "is not reachable by", human)
    return False


def robot_wait_for_human_to_tidy(agents, self_state, self_name):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @return:
    @semantic_name: wait
    """
    return agents

def robot_congratulate(agents, self_state, self_name, human):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @param human:
    @return:
    @semantic_name: congratulate
    """
    return agents


def human_pick_cube(agents, self_state, self_name, cube):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @param cube:
    @return:
    @semantic_name: pick_cube
    @ontology_type cube: Cube
    """
    if self_name in self_state.isReachableBy[cube] and self_state.isHolding[self_name] == []:
        for a in agents.values():
            a.state.isInContainer[cube] = []
            a.state.isHolding[self_name] = [cube]
            a.state.isHeldBy[cube] = [self_name]
        return agents
    return False


def human_drop_cube(agents, self_state, self_name, box):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @param box:
    @return:
    @semantic_name: drop_in_container
    """
    if len(self_state.isHolding[self_name]) == 1:
        for a in agents.values():
            cube = a.state.isHolding[self_name][0]
            a.state.isInContainer[cube] = [box]
            a.state.isHolding[self_name] = []
            a.state.isHeldBy[cube] = []
        return agents
    return False


# As we don't know the agents name in advance, we store the operators here, until a ros plan call
ctrl_operators = [robot_tell_human_to_tidy, robot_wait_for_human_to_tidy, robot_congratulate]
unctrl_operators = [human_pick_cube, human_drop_cube]


def robot_wait_human(agents, self_state, self_name, cube, box, human):
    if self_state.isHolding[human] == [] and box in self_state.isInContainer[cube]:
        return []
    if same_last_tasks(agents[self_name].plan, 3, "robot_wait_for_human_to_tidy"):
        print("Same last tasks")
        print(agents["human_0"].plan)
        return False
    return [("robot_wait_for_human_to_tidy",), ("wait_for_human", cube, box, human)]


def robot_tidy_one(agents, self_state, self_name, cube, box, human):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @param cube:
    @return:
    @ontology_type cube: Cube
    """
    return [("robot_tell_human_to_tidy", human, cube, box), ("wait_for_human", cube, box, human)]


def robot_tidy(agents, self_state, self_name, goal):
    """
    @param agents:
    @param self_state:
    @param self_name:
    @return:
    """
    hatpehda.print_goal(goal)
    cubes_boxes_cost = []
    human = "human"
    for ag in agents:
        if ag != self_name:
            human = ag
            break

    print("Human name:", human)

    for c, boxes in goal.isInContainer.items():
        if boxes[0] in self_state.isInContainer[c]:
            continue
        ctx = [("?0", "isAbove", "table_1")]
        symbols = {"?0": c}
        reg = regHandler.get_re(human, agents[human].state, ctx, symbols, c)
        cost = 0
        if not reg.success:
            cost = -1
            raise NotImplementedError(
                "The cube '{}' is not verbally referencable, this is not supported for now.".format(c))
        else:
            cost = len(reg.sparqlResult)
        cubes_boxes_cost.append((c, boxes[0], cost))

    if cubes_boxes_cost == []:
        return []
    cubes_boxes_cost = sorted(cubes_boxes_cost, key=lambda x: x[2])
    print("cubes sorted", cubes_boxes_cost)
    for t in agents[self_name].tasks:
        print("Task: ", t.name, t.parameters)
        if t.name == "robot_congratulate" and t.parameters == (human,):
            return [('tidy_one', cubes_boxes_cost[0][0], cubes_boxes_cost[0][1], human), ("tidy_cubes", goal)]
    return [('tidy_one', cubes_boxes_cost[0][0], cubes_boxes_cost[0][1], human), ("tidy_cubes", goal), ("robot_congratulate", human)]


def human_tidy(agents, self_state, self_name, cube, box):
    """
    @semantic_name:
    @param agents:
    @param self_state:
    @param self_name:
    @param cube:
    @return:
    @ontology_type cube: Cube
    """
    return [("human_pick_cube", cube), ("human_drop_cube", box)]


# We don't know the agents name in advance so we store them here, until we can add the proper agents
ctrl_methods = [("tidy_one", robot_tidy_one), ("tidy_cubes", robot_tidy), ("wait_for_human", robot_wait_human)]
unctrl_methods = [("tidy", human_tidy)]


def on_new_plan_req(ctrl_agents, unctrl_agent):
    hatpehda.reset_planner()

    def update_agents(agents, operators, methods):
        for ag, tasks in agents.items():
            state = hatpehda.State(ag + "_init")
            state.types = {"Agent": ["isHolding"], "DtCube": ["isInContainer", "isHeldBy", "isReachableBy"],
                           "DtBox": [], "ReachableDtBox": [],
                           "ReceiverReachableDtBox": [],
                           "VisibleDtBox": [], "ReceiverVisibleDtBox": [], "DirectorVisibleDtBox": [],
                           "DirectorReachableDtBox": [], "DtDirector": [], "DtReceiver": [], "DtThrowBox": []}
            state_filled = retrieve_state_from_ontology(ag, state)

            #state_filled = state
            #state_filled.individuals = {'DtCube': ["cube_BGTG", "cube_GBTG", "cube_GGTB"], 'DtBox': ["box_C1", "box_C2", 'box_C3']}
            #state_filled.isInContainer = {'cube_BGTG': ["box_C1"], 'cube_GBTG': ['box_C2'], 'cube_GGTB': ['box_C3']}
            #state_filled.isHeldBy = {'cube_BGTG': [], 'cube_GBTG': [], 'cube_GGTB': []}

            # TODO: remove
            state_filled.individuals["DtReceiver"] = ["human_0"]
            state_filled.isHolding = {next(iter(unctrl_agent)): []}
            state_filled.isReachableBy = {c: [next(iter(unctrl_agent))] for c in state_filled.individuals["DtCube"]}

            hatpehda.declare_operators(ag, *operators)
            for me in methods:
                hatpehda.declare_methods(ag, *me)

            hatpehda.set_state(ag, state_filled)
            hatpehda.add_tasks(ag, [(t[0], *t[1]) for t in tasks])

    update_agents(ctrl_agents, ctrl_operators, ctrl_methods)
    update_agents(unctrl_agent, unctrl_operators, unctrl_methods)
    # hatpehda.print_state(hatpehda.agents["robot"].state)
    # print(hatpehda.agents["robot"].tasks)
    # hatpehda.print_methods("robot")
    # hatpehda.print_methods("human")
    sol = []

    # For now it only works with one controllable and one uncontrollable agents...
    plans = hatpehda.seek_plan_robot(hatpehda.agents, next(iter(ctrl_agents)), sol,
                                     uncontrollable_agent_name=next(iter(unctrl_agent)))
    print(len(sol))
    #regHandler.export_log("human_planning")
    gui.show_plan(sol, next(iter(ctrl_agents)), next(iter(unctrl_agent)))
    print(sol)
    rosnode.send_plan(sol, next(iter(ctrl_agents)), next(iter(unctrl_agent)))


if __name__ == "__main__":
    rosnode = RosNode.start_ros_node("planner", on_new_plan_req)
    regHandler = REGHandler()
    rosnode.wait_for_request()

    start = time.time()
    # plans = hatpehda.multi_agent_planning(verbose=0)
    end = time.time()
    regHandler.cleanup()


    # print(len(hatpehda.ma_solutions))
    # for ags in hatpehda.ma_solutions:
    #    print("Plan :", ags["robot"].global_plan, "with cost:", ags["robot"].global_plan_cost)
    # print("Took", end - start, "seconds")

    # regHandler.export_log("robot_planning")
    # regHandler.cleanup()
