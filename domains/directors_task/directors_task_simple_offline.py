#!/usr/bin/env python3

import hatpehda
from copy import deepcopy
from hatpehda import gui

from itertools import permutations
import time

### Helpers

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
        hatpehda.add_tasks(human, [("tidy", cube, box)], agents)
        return agents
    else:
        print("cube", cube, "is not reachable by", human)
    return False


def robot_yell_human_to_tidy(agents, self_state, self_name, human, cube, box):
    if human in self_state.isReachableBy[cube]:
        ctx = [("?0", "isAbove", "table_1")]
        symbols = {"?0": cube}
        hatpehda.add_tasks(human, [("human_surprise",), ("tidy", cube, box)], agents)
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

def human_throw_cube(agents, self_state, self_name, box):
    if len(self_state.isHolding[self_name]) == 1:
        for a in agents.values():
            cube = a.state.isHolding[self_name][0]
            a.state.isInContainer[cube] = [box]
            a.state.isHolding[self_name] = []
            a.state.isHeldBy[cube] = []
        return agents
    return False

def human_surprise(agents, self_state, self_name):
    return agents


# As we don't know the agents name in advance, we store the operators here, until a ros plan call
ctrl_operators = [robot_tell_human_to_tidy, robot_wait_for_human_to_tidy, robot_congratulate, robot_yell_human_to_tidy]
unctrl_operators = [human_pick_cube, human_drop_cube, human_throw_cube, human_surprise]


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

def robot_yell_tidy_one(agents, self_state, self_name, cube, box, human):
    return [("robot_yell_human_to_tidy", human, cube, box), ("wait_for_human", cube, box, human)]

@hatpehda.multi_decomposition
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

    for c, boxes in goal.isInContainer.items():
        if boxes[0] in self_state.isInContainer[c]:
            continue
        cubes_boxes_cost.append((c, boxes[0], 1))

    tasks = []
    for perm in permutations(cubes_boxes_cost):
        t = []
        for p in perm:
            t.append(('tidy_one', p[0], p[1], human))
        t.append(("robot_congratulate", human))
        tasks.append(t)
    return tasks

    # if cubes_boxes_cost == []:
    #     return []
    # cubes_boxes_cost = sorted(cubes_boxes_cost, key=lambda x: x[2])
    # for t in agents[self_name].tasks:
    #     if t.name == "robot_congratulate" and t.parameters == (human,):
    #         return [('tidy_one', cubes_boxes_cost[0][0], cubes_boxes_cost[0][1], human), ("tidy_cubes", goal)]
    # return [('tidy_one', cubes_boxes_cost[0][0], cubes_boxes_cost[0][1], human), ("tidy_cubes", goal), ("robot_congratulate", human)]


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
    return [("human_pick_cube", cube), ("human_store", box)]



# We don't know the agents name in advance so we store them here, until we can add the proper agents
ctrl_methods = [("tidy_one", robot_tidy_one, robot_yell_tidy_one), ("tidy_cubes", robot_tidy), ("wait_for_human", robot_wait_human)]
unctrl_methods = [("tidy", human_tidy), ("human_store", lambda a, s, n, box: [("human_drop_cube", box)], lambda a, s, n, box: [("human_throw_cube", box)])]

def get_first_action(last_action):
    action = last_action
    while action is not None:
        if action.previous is None:
            return action
        action = action.previous

def get_last_actions(action):
    if action.next is None or action.next == []:
        return [action]
    actions = []
    for act in action.next:
        actions += get_last_actions(act)
    return actions

def select_policies(first_action):

    def explore_policy(action, cost):
        if action.next is None or action.next == []:
            return cost + 1

        if action.agent == "robot":
            total_cost = 0
            for successor in action.next:
                total_cost += explore_policy(successor, cost + 1)
            return total_cost / len(action.next)

        elif action.agent == "human":
            min_cost = explore_policy(action.next[0], cost + 1)
            min_i_cost = 0
            for i, successor in enumerate(action.next[1:]):
                new_cost = explore_policy(successor, cost + 1)
                if new_cost < min_cost:
                    min_i_cost = i + 1
                    min_cost = new_cost
            action.next = [action.next[min_i_cost]]
            action.next[min_i_cost].predecessor = action
            return min_cost

    act = deepcopy(first_action)
    cost = explore_policy(act, 1)
    return cost, act

if __name__ == "__main__":

    start = time.time()

    state = hatpehda.State("robot_init")
    state.types = {"Agent": ["isHolding"], "DtCube": ["isInContainer", "isHeldBy", "isReachableBy"],
                   "DtBox": [], "ReachableDtBox": [],
                   "ReceiverReachableDtBox": [],
                   "VisibleDtBox": [], "ReceiverVisibleDtBox": [], "DirectorVisibleDtBox": [],
                   "DirectorReachableDtBox": [], "DtDirector": [], "DtReceiver": [], "DtThrowBox": []}
    state_filled = state
    state_filled.individuals = {'DtCube': ["cube_BGTG", "cube_GBTG", "cube_GGTB"], 'DtBox': ["box_C1", "box_C2", 'box_C3']}
    state_filled.isInContainer = {'cube_BGTG': ["box_C1"], 'cube_GBTG': ['box_C2'], 'cube_GGTB': ['box_C3']}
    state_filled.isHeldBy = {'cube_BGTG': [], 'cube_GBTG': [], 'cube_GGTB': []}
    state_filled.individuals["DtReceiver"] = ["human_0"]
    state_filled.isHolding = {"human": []}
    state_filled.isReachableBy = {c: ["human"] for c in state_filled.individuals["DtCube"]}

    hatpehda.declare_operators("robot", *ctrl_operators)
    for me in ctrl_methods:
        hatpehda.declare_methods("robot", *me)
    hatpehda.declare_operators("human", *unctrl_operators)
    for me in unctrl_methods:
        hatpehda.declare_methods("human", *me)

    robot_goal = hatpehda.Goal("robot_goal")
    robot_goal.isInContainer = {"cube_BGTG": ["throw_box_green"], "cube_GBTG": ["throw_box_green"]}

    hatpehda.set_state("robot", state_filled)
    hatpehda.add_tasks("robot", [("tidy_cubes", robot_goal)])

    human_state = deepcopy(state_filled)
    human_state.__name__ = "human_init"
    hatpehda.set_state("human", human_state)


    sols = []
    fails = []
    hatpehda.seek_plan_robot(hatpehda.agents, "robot", sols, "human", fails)
    end = time.time()

    print(len(sols))

    gui.show_plan(sols, "robot", "human")
    #rosnode = ros.RosNode.start_ros_node("planner", lambda x: print("plop"))
    #time.sleep(5)
    #rosnode.send_plan(sols, "robot", "human")
    input()
    first_action = get_first_action(sols[0])
    cost, action = select_policies(first_action)
    gui.show_plan(get_last_actions(action), "robot", "human")
    print("policy cost", cost)

    # print(len(hatpehda.ma_solutions))
    # for ags in hatpehda.ma_solutions:
    #    print("Plan :", ags["robot"].global_plan, "with cost:", ags["robot"].global_plan_cost)
    # print("Took", end - start, "seconds")

    # regHandler.export_log("robot_planning")
    # regHandler.cleanup()

