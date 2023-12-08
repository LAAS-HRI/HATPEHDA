#!/usr/bin/env python3

import hatpehda
from copy import deepcopy
from hatpehda import gui



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

def robot_heat_water(agents, self_state, self_name, mug):
    return False


def robot_get_instant_coffee(agents, self_state, self_name, human):
    return False

def robot_pour_heated_water(agents, self_state, self_name):
    return False

def robot_pour_instant_coffee(agents, self_state, self_name):
    return agents

def robot_ask_human_to_make_coffee(agents, self_state, self_name, human):
    return False

def robot_ask_human_to_make_coffee(agents, self_state, self_name, human):
    return False

def human_verbally_answer_right_mug(agents, self_state, self_name, robot, mug):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @return:
    @semantic_name: wait
    """
    if mug == "mug_0" or mug == "mug_1":
        return False
    for a in agents.values():
        a.state.isOwnedBy[mug] = self_name
    return agents

def human_complain_mug(agents, self_state, self_name, robot, mug):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @param human:
    @return:
    @semantic_name: congratulate
    """
    for a in agents.values():
        mug = a.state.isHolding[robot]
        if mug is not None and mug != []:
            mug, = mug
            a.state.isNotOwnedBy[mug] = self_name
    return agents


# As we don't know the agents name in advance, we store the operators here, until a ros plan call
ctrl_operators = [robot_pick_mug, robot_drop_mug, robot_ask_mug_to_take, robot_go_to_coffee_machine]
unctrl_operators = [human_verbally_answer_right_mug, human_complain_mug]

cost_dict = {"robot_pick_mug": 1, "robot_drop_mug": 1, "robot_ask_mug_to_take": 1, "robot_go_to_coffee_machine": 1,
             "human_verbally_answer_right_mug": 2, "human_complain_mug": 1, "IDLE": 0, "BEGIN": 0}


def robot_ask_take_mug(agents, self_state, self_name, human):
    if same_last_tasks(agents[human].plan, 3, "WAIT"):
        return False
    for mug, h in self_state.isOwnedBy.items():
        if h == human:
            return [("robot_pick_mug", mug)]
    for mug in self_state.individuals["Mug"]:
        if mug not in self_state.isNotOwnedBy or human not in self_state.isNotOwnedBy[mug]:
            return [("robot_ask_mug_to_take", human), ("robot_get_right_mug", human)]
    return False

@hatpehda.multi_decomposition
def robot_take_one_random_mug(agents, self_state, self_name, human):
    """

    @param agents:
    @param self_state:
    @param self_name:
    @param cube:
    @return:
    @ontology_type cube: Cube
    """
    if same_last_tasks(agents[human].plan, 3, "WAIT"):
        return False
    for mug, h in self_state.isOwnedBy.items():
        if h == human:
            return False
    task_list = []
    for mug in self_state.individuals["Mug"]:
        if mug not in self_state.isNotOwnedBy or human not in self_state.isNotOwnedBy[mug]:
            task_list.append([("robot_pick_mug", mug)])
    if task_list == []:
        return False
    return task_list


def human_agree_mug_taken(agents, self_state, self_name, robot, mug):
    """
    @semantic_name:
    @param agents:
    @param self_state:
    @param self_name:
    @param cube:
    @return:
    @ontology_type cube: Cube
    """
    return []

def human_disagree_mug_taken(agents, self_state, self_name, robot, mug):
    """
    @semantic_name:
    @param agents:
    @param self_state:
    @param self_name:
    @param cube:
    @return:
    @ontology_type cube: Cube
    """
    return [("human_complain_mug", robot, mug)]

@hatpehda.multi_decomposition
def human_answer_mug(agents, self_state, self_name, robot):
    """
    @semantic_name:
    @param agents:
    @param self_state:
    @param self_name:
    @param cube:
    @return:
    @ontology_type cube: Cube
    """
    for mug, h in self_state.isOwnedBy.items():
        if h == self_name:
            return [[("human_verbally_answer_right_mug", robot, mug)]]
    task_list = []
    for mug in self_state.individuals["Mug"]:
        if mug not in self_state.isNotOwnedBy or self_name not in self_state.isNotOwnedBy[mug]:
            task_list.append([("human_verbally_answer_right_mug", robot, mug)])
    if task_list == []:
        return False
    return task_list



# We don't know the agents name in advance so we store them here, until we can add the proper agents
ctrl_methods = [("robot_get_right_mug", robot_take_one_random_mug, robot_ask_take_mug)]
unctrl_methods = [("human_answer_mug_a", human_answer_mug), ("human_check_mug_taken", human_agree_mug_taken, human_disagree_mug_taken)]


# Triggers
def human_check_mug(agents, self_state, self_name):
    if agents["robot"].plan[-1].name == "robot_pick_mug":
        mug = self_state.isHolding["robot"][0]
        if mug in self_state.isNotOwnedBy and self_state.isNotOwnedBy[mug] == self_name:
            return False
        for action in agents[self_name].plan:
            if action.name == "human_verbally_answer_right_mug" and action.parameters[1] == mug:
                return False
        return [("human_check_mug_taken", "robot", mug)]
    return False

def robot_check_wrong_mug(agents, self_state, self_name):
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        heldMug = self_state.isHolding[self_name][0]
        if heldMug in self_state.isNotOwnedBy and "human" == self_state.isNotOwnedBy[heldMug]:
            return [("robot_drop_mug", ), ("robot_get_right_mug", "human")]
    return False

ctrl_triggers = [robot_check_wrong_mug]
unctrl_triggers = [human_check_mug]

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
            return cost + cost_dict[action.name]

        if action.agent == "robot":
            total_cost = 0
            for successor in action.next:
                total_cost += explore_policy(successor, cost + cost_dict[action.name])
            return total_cost / len(action.next)

        elif action.agent == "human":
            min_cost = explore_policy(action.next[0], cost + cost_dict[action.name])
            min_i_cost = 0
            for i, successor in enumerate(action.next[1:]):
                new_cost = explore_policy(successor, cost + cost_dict[action.name])
                if new_cost < min_cost:
                    min_i_cost = i + 1
                    min_cost = new_cost
            action.next = [action.next[min_i_cost]]
            print("min_cost", min_cost)
            action.next[0].predecessor = action
            return min_cost

    act = deepcopy(first_action)
    cost = explore_policy(act, 0)
    return cost, act

if __name__ == "__main__":

    n_mug = 3
    start = time.time()

    state = hatpehda.State("robot_init")
    state.types = {"Agent": ["isHolding"], "Mug": ["isHeldBy", "isReachableBy"]}
    state_filled = state
    state_filled.individuals = {'Mug': ["mug_{}".format(i) for i in range(n_mug)]}
    state_filled.isHeldBy = {m: [] for m in state_filled.individuals["Mug"]}
    state_filled.isHolding = {"human": [], "robot": []}
    state_filled.isOwnedBy = {}
    state_filled.isNotOwnedBy = {}
    state_filled.isReachableBy = {m: ["human", "robot"] for m in state_filled.individuals["Mug"]}
    state_filled.notReferrableMugs = {"mug_0": ["mug_1"], "mug_1": ["mug_0"]}

    hatpehda.declare_operators("robot", *ctrl_operators)
    for me in ctrl_methods:
        hatpehda.declare_methods("robot", *me)
    hatpehda.declare_triggers("robot", *ctrl_triggers)
    hatpehda.declare_operators("human", *unctrl_operators)
    for me in unctrl_methods:
        hatpehda.declare_methods("human", *me)
    hatpehda.declare_triggers("human", *unctrl_triggers)

    #robot_goal = hatpehda.Goal("robot_goal")
    #robot_goal.isInContainer = {"cube_BGTG": ["throw_box_green"], "cube_GBTG": ["throw_box_green"]}

    hatpehda.set_state("robot", state_filled)
    hatpehda.add_tasks("robot", [("robot_get_right_mug", "human"), ("robot_go_to_coffee_machine",)])

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
    begin_action = hatpehda.Operator("BEGIN", [], "human", None, None, None)
    for s in sols:
        first_action = get_first_action(s)
        if s.name != "BEGIN":
            s.predecessor = begin_action
            begin_action.next.append(first_action)
    cost, action = select_policies(begin_action)
    gui.show_plan(get_last_actions(action), "robot", "human")
    print("policy cost", cost)

    # print(len(hatpehda.ma_solutions))
    # for ags in hatpehda.ma_solutions:
    #    print("Plan :", ags["robot"].global_plan, "with cost:", ags["robot"].global_plan_cost)
    # print("Took", end - start, "seconds")

    # regHandler.export_log("robot_planning")
    # regHandler.cleanup()

