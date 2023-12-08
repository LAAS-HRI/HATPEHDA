#!/usr/bin/env python3

import hatpehda
from copy import deepcopy
from hatpehda import gui
from hatpehda.reg_mock import REGHandler



import time

regHandler = None

### Helpers

def same_last_tasks(plan, n, task=None):
    """
    Given a partial 'plan', returns True if the 'n' last tasks of the partial plan are the same (and optionnaly equal to 'task')
    """
    if len(plan) < n:
        return False
    last_tasks = [plan[-i].name for i in range(1, n + 1)]
    #print("Last tasks:", last_tasks)
    if task is not None and last_tasks[0] != task:
        return False
    return last_tasks.count(last_tasks[0]) == len(last_tasks)

### Primitive tasks

def robot_pick_mug(agents, self_state, self_name, mug):
    """
    Checks if the 'mug' is reachable by the agent (robot) and if the agent does not carry anything.
    Then updates the beliefs of all the agents in the same room as the robot as for the robot having picked the 'mug'
    """
    if self_name in self_state.isReachableBy[mug] and self_state.isHolding[self_name] == []:
        robot_room = self_state.isInRoom[self_name][0]
        for agent_name in self_state.agentsInRoom[robot_room]:
            a = agents[agent_name]
            a.state.isReachableBy[mug] = []
            a.state.isHolding[self_name] = [mug]
            a.state.isHeldBy[mug] = [self_name]
        return agents
    return False


def robot_ask_mug_to_take(agents, self_state, self_name, human):
    """
    Asks the 'human' which one is their mug by adding to their agenda that they will answer the question.
    Note that we could have checked if the communication was feasible
    """
    hatpehda.add_tasks(human, [("human_answer_mug_a", self_name)], agents)
    return agents

def robot_drop_mug(agents, self_state, self_name):
    """
    Checks if the robot is holding something.
    If so, update all the agents in the room beliefs with the fact that the robot as dropped what they thought it was holding.
    """
    if self_state.isHolding[self_name] != []:
        robot_room = self_state.isInRoom[self_name][0]
        for agent_name in self_state.agentsInRoom[robot_room]:
            a = agents[agent_name]
            mug = a.state.isHolding[self_name]
            if mug != []:
                mug, = mug
                a.state.isReachableBy[mug] = [self_name]
                a.state.isHolding[self_name] = []
                a.state.isHeldBy[mug] = []
        return agents
    return False

def robot_go_to_coffee_machine(agents, self_state, self_name):
    """
    This action has no effect nor preconditions. It only represents the robot leaving the room (for the example)
    """
    return agents

def human_verbally_answer_right_mug(agents, self_state, self_name, robot, mug):
    """

    """
    # We make a REG request to check if we estimate that the human will be able to refer to their mug
    ctx = [("?0", "isAbove", "table_1")]
    symbols = {"?0": mug}
    # This function copy the ontology of 'self_name' (human), update it with beliefs from 'self_state' and runs
    # a REG request with 'ctx' and 'symbols' as context with the target entity 'mug'
    reg = regHandler.get_re(self_name, self_state, ctx, symbols, mug)
    if not reg.success:
        return False

    human_room = self_state.isInRoom[self_name][0]
    for agent_name in self_state.agentsInRoom[human_room]:
        a = agents[agent_name]
        a.state.isOwnedBy[mug] = self_name
    return agents

def human_complain_mug(agents, self_state, self_name, robot, mug):
    """
    This primitive task models the human complaining about 'mug' not being theirs. We update all the agents in the
    room beliefs, with the 'mug' not being the one 'self_name' (human)
    """
    human_room = self_state.isInRoom[self_name][0]
    for agent_name in self_state.agentsInRoom[human_room]:
        a = agents[agent_name]
        mug = a.state.isHolding[robot]
        if mug is not None and mug != []:
            mug, = mug
            a.state.isNotOwnedBy[mug] = self_name
    return agents


# As we don't know the agents name in advance, we store the operators here, until a ros plan call
ctrl_operators = [robot_pick_mug, robot_drop_mug, robot_ask_mug_to_take, robot_go_to_coffee_machine]
unctrl_operators = [human_verbally_answer_right_mug, human_complain_mug]

cost_dict = {"robot_pick_mug": 1, "robot_drop_mug": 1, "robot_ask_mug_to_take": 1, "robot_go_to_coffee_machine": 1,
             "human_verbally_answer_right_mug": 2, "human_complain_mug": 10, "IDLE": 0, "BEGIN": 0}


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

if __name__ == "__main__":
    regHandler = REGHandler()

    n_mug = 2
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
    state_filled.agentsInRoom = {"office": ["human", "robot"]}
    state_filled.isInRoom = {"human": ["office"], "robot": ["office"]}
    #state_filled.notReferrableMugs = {"mug_0": ["mug_1"], "mug_1": ["mug_0"]}
    state_filled.notReferrableMugs = {}

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
    start_explore = time.time()
    hatpehda.seek_plan_robot(hatpehda.agents, "robot", sols, "human", fails)
    end_explore = time.time()

    print(len(sols))

    #gui.show_plan(sols, "robot", "human")
    #rosnode = ros.RosNode.start_ros_node("planner", lambda x: print("plop"))
    #time.sleep(5)
    #rosnode.send_plan(sols, "robot", "human")
    cost, root_action = hatpehda.select_conditional_plan(sols, "robot", "human", cost_dict)
    gui.show_plan(hatpehda.get_last_actions(root_action), "robot", "human")
    print("policy cost", cost)

    #print("n mug: {}\texplore duration: {}sec\tselect duration: {}sec\tnumber of valid branches: {}".format(n_mug, end_explore - start_explore, end_select - start_select, len(sols)))

    # print(len(hatpehda.ma_solutions))
    # for ags in hatpehda.ma_solutions:
    #    print("Plan :", ags["robot"].global_plan, "with cost:", ags["robot"].global_plan_cost)
    # print("Took", end - start, "seconds")

    # regHandler.export_log("robot_planning")
    # regHandler.cleanup()

