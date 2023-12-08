#!/usr/bin/env python

import hatpehda

from hatpehda.standard_domains import  generate_standard_domain

import rospy
from std_msgs.msg import String

from ontologenius import OntologiesManipulator, OntologyManipulator

from typing import Dict

from functools import partial, update_wrapper
from itertools import permutations
from copy import deepcopy

from hatpehda.reg import REGHandler

from hatpehda.ros import RosNode

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

def get_box_containing_cube(state, cube):
    box = None
    if cube in state.isIn and state.isIn[cube] != []:
        for container in state.isIn[cube]:
            if container in state.individuals["Box"]:
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
    #onto = OntologyManipulator()
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

def robot_tell_human_to_tidy(agents, self_state, self_name, human, cube):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @param human:
    @param cube:
    @return:
    @ontology_type human: Human
    @ontology_type cube: Cube
    """
    if is_cube_pickable_by(self_state, human, cube):
        ctx = [("?0", "isOnTopOf", "table_1")]
        symbols = {"?0": cube}
        reg = regHandler.get_re(self_name, self_state, ctx, symbols, cube)
        if not reg.success:
            return False
        cost = len(reg.sparqlResult)
        agents[human].tasks.insert(0, ("tidy", cube))
        return agents, cost
    return False

def robot_wait_for_human_to_tidy(agents, self_state, self_name, human, cube):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @param human:
    @param cube:
    @return:
    @ontology_type human: Human
    @ontology_type cube: Cube
    """
    # Todo: Check if in goal box
    if self_state.isIn[cube] == [] and self_state.isHolding[human] == [] and self_state.isHeldBy[cube] == []:
        return agents, 0.
    return False


def human_pick_cube(agents, self_state, self_name, cube):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @param cube:
    @return:
    @ontology_type cube: Cube
    """
    if is_cube_pickable_by(self_state, self_name, cube) and self_state.isHolding[self_name] == []:
        for a in agents.values():
            a.state.isIn[cube] = []
            a.state.isHolding[self_name] = [cube]
            a.state.isHeldBy[cube] = [self_name]
        return agents, 1.
    return False

def human_drop_cube(agents, self_state, self_name):
    if len(self_state.isHolding[self_name]) == 1:
        for a in agents.values():
            cube = a.state.isHolding[self_name][0]
            a.state.isIn[cube] = []  # TODO: Add the goal box
            a.state.isHolding[self_name] = []
            a.state.isHeldBy[cube] = []
        return agents, 1.
    return False

hatpehda.declare_operators("robot", robot_tell_human_to_tidy, robot_wait_for_human_to_tidy)
hatpehda.declare_operators("human", human_pick_cube, human_drop_cube)

def robot_tidy_one(angents, self_state, self_name, cube):
    """

    @param angents:
    @param self_state:
    @param self_name:
    @param cube:
    @return:
    @ontology_type cube: Cube
    """
    return [("robot_tell_human_to_tidy", "human", cube), ("robot_wait_for_human_to_tidy", "human", cube)]

def robot_tidy(agents, self_state, self_name, order):
    """
    @param agents:
    @param self_state:
    @param self_name:
    @param order:
    @return:
    """
    actions = [("tidy_one", c) for c in order]
    return actions

def human_tidy(agents, self_state, self_name, cube):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @param cube:
    @return:
    @ontology_type cube: Cube
    """
    return [("human_pick_cube", cube), ("human_drop_cube",)]

def generate_tidy_all_orders(cubes_to_tidy):
    fns = []
    for order in permutations(cubes_to_tidy):
        fn = partial(robot_tidy, order=order)
        update_wrapper(fn, robot_tidy)
        fns.append(fn)
    hatpehda.declare_methods("robot", "tidy", *fns)

hatpehda.declare_methods("robot", "tidy_one", robot_tidy_one)
hatpehda.declare_methods("human", "tidy", human_tidy)





def on_new_plan_req(agents):
    for ag, tasks in agents.items():
        state = hatpehda.State(ag + "_init")
        state.types = {"Agent": ["isHolding"], "Cube": ["isIn", "isHeldBy"], "Box": [], "ReachableDtBox": [],
                         "ReceiverReachableDtBox": [],
                         "VisibleDtBox": [], "ReceiverVisibleDtBox": [], "DirectorVisibleDtBox": [],
                         "DirectorReachableDtBox": [], "DtDirector": [], "DtReceiver": []}
        # state_r = retrieve_state_from_ontology("robot", state_r)

        state.individuals = {}
        state.isHolding = {}
        state.individuals["DtReceiver"] = ["human"]
        state.isHolding["human"] = []

        state_h = deepcopy(state)  # TODO: Retrieve it from the ontology
        generate_tidy_all_orders(["cube_GBTG", "cube_BBTG", "cube_GBCG", "cube_GBTB"])
        hatpehda.set_state(ag, state)
        hatpehda.add_tasks(ag, [(t[0], *t[1]) for t in tasks])

    hatpehda.print_state(hatpehda.agents["robot"].state)
    print(hatpehda.agents["robot"].tasks)
    hatpehda.print_methods("robot")
    hatpehda.print_methods("human")
    sol = []
    plans = hatpehda.seek_plan_robot(hatpehda.agents, "robot", sol)
    print(len(hatpehda.ma_solutions))







if __name__ == "__main__":

    #regHandler = REGHandler()



    rosnode = RosNode.start_ros_node("planner", on_new_plan_req)
    rosnode.wait_for_request()


    start = time.time()
    #plans = hatpehda.multi_agent_planning(verbose=0)
    end = time.time()
    #print(len(hatpehda.ma_solutions))
    #for ags in hatpehda.ma_solutions:
    #    print("Plan :", ags["robot"].global_plan, "with cost:", ags["robot"].global_plan_cost)
    #print("Took", end - start, "seconds")

    #regHandler.export_log("robot_planning")
    #regHandler.cleanup()

