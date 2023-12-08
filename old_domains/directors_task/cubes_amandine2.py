#!/usr/bin/env python3

import hatpehda
from copy import deepcopy
from hatpehda import gui
from hatpehda.reg_mock import REGHandler
from hatpehda import ros



import time

regHandler = None
r_node = None

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

def robot_pick_cube(agents, self_state, self_name, pickable):
    if self_name in self_state.isReachableBy[pickable] and self_state.isHolding[self_name] == []:
        for agent_name in agents:
            a = agents[agent_name]
            a.state.isReachableBy[pickable] = []
            a.state.isHolding[self_name] = [pickable]
            a.state.isHeldBy[pickable] = [self_name]
        return agents
    return False


def robot_place_cube(agents, self_state, self_name, pickable, support):
    if self_state.hasOn[support] != []:
        return False
    if self_state.isOn[support] == []:
        return False
    if self_state.isHolding[self_name] != []:
        for agent_name in agents:
            a = agents[agent_name]
            a.state.isHolding[self_name] = []
            a.state.isHeldBy[pickable] = []
            a.state.isOn[pickable] = [support]
            a.state.hasOn[support] = [pickable]
        return agents
    return False

def robot_wait(agents, self_state, self_name):
    return agents

def human_pick_cube(agents, self_state, self_name, pickable):
    if self_name in self_state.isReachableBy[pickable] and self_state.isHolding[self_name] == []:
        for agent_name in agents:
            a = agents[agent_name]
            a.state.isReachableBy[pickable] = []
            a.state.isHolding[self_name] = [pickable]
            a.state.isHeldBy[pickable] = [self_name]
        return agents
    return False

def human_place_cube(agents, self_state, self_name, pickable, support):
    if self_state.hasOn[support] != []:
        return False
    if self_state.isOn[support] == []:
        return False
    if self_state.isHolding[self_name] != []:
        for agent_name in agents:
            a = agents[agent_name]
            a.state.isHolding[self_name] = []
            a.state.isHeldBy[pickable] = []
            a.state.isOn[pickable] = [support]
            a.state.hasOn[support] = [pickable]
        return agents
    return False

def human_place_stick(agents, self_state, self_name, stick, support1, support2):
    if self_state.isOn[support1] != [] and self_state.isOn[support2] != []:
        if self_state.isHolding[self_name] != []:
            for agent_name in agents:
                a = agents[agent_name]
                a.state.isHolding[self_name] = []
                a.state.isHeldBy[stick] = []
                a.state.isOn[stick] = [support1, support2]
                a.state.hasOn[support1] = [stick]
                a.state.hasOn[support2] = [stick]
            return agents
    return False

def human_wait_for_cube(agents, self_state, self_name):
    return agents


# As we don't know the agents name in advance, we store the operators here, until a ros plan call
ctrl_operators = [robot_pick_cube, robot_place_cube, robot_wait]
unctrl_operators = [human_pick_cube, human_place_cube, human_place_stick, human_wait_for_cube]

cost_dict = {"robot_pick_cube": 1, "robot_place_cube": 1, "robot_wait": 1, "human_place_stick":1, "human_wait_for_cube":1,
             "human_pick_cube": 1, "human_place_cube": 1, "WAIT": 1, "IDLE": 0, "BEGIN": 0}

def robot_make_stack2(agents, self_state, self_name):
    return [("robot_pick_cube", "red_cube_1"), ("robot_wait",), ("place_red_cube", "red_cube_1"), ("wait_stick",), ("robot_wait", ), ("place_blue_cube1", "blue_cube_1"),
          ("robot_place_green_cube", "green_cube",), ("place_blue_cube2", "blue_cube_1"), ("assert_plan_over",)]

@hatpehda.multi_decomposition
def robot_place_red_cube(agents, self_state, self_name, cube):
    if self_state.isOn[cube] != []:
        return []
    return [[("robot_place_cube", cube, "placement_1")], [("robot_place_cube", cube, "placement_2")]]

def robot_wait_stick(agents, self_state, self_name):
    if self_state.isOn["stick"] == []:
        return [("robot_wait",), ("wait_stick",)]
    else:
        return []

def robot_place_blue_cube1(agents, self_state, self_name, cube):
    other_agent = None
    for agent in agents:
        if agent == self_name:
            continue
        other_agent = agent
    if self_state.hasOn["stick"] == [] and agents[other_agent].plan[-1].name == "human_wait_for_cube":
        return [("robot_pick_cube", cube), ("robot_place_cube", cube, "stick"), ("robot_pick_cube", "green_cube")]
    else:
        return [("robot_pick_cube", "green_cube"), ("wait_blue_cube",)]

def robot_place_blue_cube2(agents, self_state, self_name, cube):
    if self_state.isOn[cube] != []:
        return []
    else:
        return [("robot_pick_cube", cube), ("robot_place_cube", cube, "green_cube")]

def robot_wait_blue_cube(agents, self_state, self_name):
    if same_last_tasks(agents[self_name].plan, 10, "robot_wait"):
        return False
    if self_state.hasOn["stick"] != []:
        return []
    else:
        return [("robot_wait",), ("wait_blue_cube",)]

def robot_place_green_cube(agents, self_state, self_name, cube):
    if self_state.isOn["blue_cube_1"] != []:
        return [("robot_place_cube", cube, "blue_cube_1")]
    elif self_state.isOn["blue_cube_2"] != []:
        return [("robot_place_cube", cube, "blue_cube_2")]
    return False

def robot_assert_plan_over(agents, self_state, self_name):
    if self_state.hasOn["green_cube"] == []:
        return [("robot_wait",), ("assert_plan_over",)]
    else:
        return []

def human_make_stack(agents, self_state, self_name):
    return [("human_pick_cube", "red_cube_2"), ("h_place_red_cube", "red_cube_2"), ("human_pick_cube", "stick"), ("human_place_stick", "stick", "red_cube_1", "red_cube_2"),
            ("h_handle_blue_cube1", "blue_cube_2"), ("h_handle_blue_cube2", "blue_cube_2")]

@hatpehda.multi_decomposition
def human_place_red_cube(agents, self_state, self_name, cube):
    tasks = []
    if self_state.hasOn["placement_1"] == []:
        tasks.append([("human_place_cube", cube, "placement_1")])
    if self_state.hasOn["placement_2"] == []:
        tasks.append([("human_place_cube", cube, "placement_2")])
    return tasks

def human_wait_red_cube(agents, self_state, self_name, cube):
    print(agents[self_name].plan[-1].name)
    if agents[self_name].plan[-1].name == "human_wait_for_cube":
        return False
    else:
        return [("human_wait_for_cube",), ("h_place_red_cube", cube)]

def human_handle_blue_cube_1_wait(agents, self_state, self_name, cube):
    if self_state.hasOn["stick"] == []:
        return [("human_wait_for_cube",)]
    else:
        return []

def human_handle_blue_cube_1_pick_place(agents, self_state, self_name, cube):
    return [("human_pick_cube", cube), ("human_place_cube", cube, "stick")]

def human_handle_blue_cube_2(agents, self_state, self_name, cube):
    if self_state.isOn[cube] != []:
        return []
    elif self_state.isOn["green_cube"] == []:
        return False
    else:
        return [("human_pick_cube", cube), ("human_place_cube", cube, "green_cube")]

def human_wait_green_cube(agents, self_state, self_name):
    return [("human_wait_cube", )] * 2

def human_place_blue_cube(agents, self_state, self_name, cube):
    return [("human_place_cube", cube, "stick")]

def human_wait_for_robot(agents, self_state, self_name):
    if same_last_tasks(agents[self_name].plan, 5, "human_wait"):
        return False
    if self_state.hasOn["stick"] != []:
        return []
    else:
        return [("human_wait_for_cube",), ("human_wait_cube",)]



# We don't know the agents name in advance so we store them here, until we can add the proper agents
ctrl_methods = [("place_red_cube", robot_place_red_cube), ("wait_stick", robot_wait_stick), ("place_blue_cube1", robot_place_blue_cube1), ("place_blue_cube2", robot_place_blue_cube2),
                ("wait_blue_cube", robot_wait_blue_cube), ("r_make_stack", robot_make_stack2), ("robot_place_green_cube", robot_place_green_cube), ("assert_plan_over", robot_assert_plan_over)]
unctrl_methods = [("h_place_red_cube", human_place_red_cube, human_wait_red_cube), ("h_handle_blue_cube1", human_handle_blue_cube_1_pick_place, human_handle_blue_cube_1_wait), ("h_make_stack", human_make_stack),
                  ("human_wait_cube", human_wait_for_robot), ("h_handle_blue_cube2", human_handle_blue_cube_2)]

def on_plan_request(ctrl_agent_task, unctrl_agent_task):
    if len(ctrl_agent_task.keys()) != 1:
        print("Only supports one ctrlable agent")
        return
    if len(unctrl_agent_task.keys()) != 1:
        print("Only supports one unctrlable agent")
        return
    robot_name = "robot"
    human_name = "human"
    state = hatpehda.State("robot_init")
    state.types = {"Agent": ["isHolding"], "Cube": ["isHeldBy", "isReachableBy"],
                   "Stick": ["isHeldBy", "isReachableBy"]}
    state_filled = state
    state_filled.individuals = {"Cube": ["red_cube_1", "red_cube_2", "blue_cube_1", "blue_cube_2", "green_cube"], "Stick": ["stick"]}
    state_filled.isHeldBy = {m: [] for m in state_filled.individuals["Cube"] + state_filled.individuals["Stick"]}
    state_filled.isHolding = {human_name: [], robot_name: []}
    state_filled.isReachableBy = {m: [human_name, robot_name] for m in
                                  state_filled.individuals["Cube"] + state_filled.individuals["Stick"]}
    state_filled.isOn = {m: [] for m in state_filled.individuals["Cube"] + state_filled.individuals["Stick"]}
    state_filled.isOn.update({"placement_1": ["table_1"], "placement_2": ["table_1"]})
    state_filled.hasOn = {m: [] for m in state_filled.individuals["Cube"] + state_filled.individuals["Stick"]}
    state_filled.hasOn.update({"placement_1": [], "placement_2": []})

    hatpehda.declare_operators(robot_name, *ctrl_operators)
    for me in ctrl_methods:
        hatpehda.declare_methods(robot_name, *me)
    # hatpehda.declare_triggers("robot", *ctrl_triggers)
    hatpehda.declare_operators(human_name, *unctrl_operators)
    for me in unctrl_methods:
        hatpehda.declare_methods(human_name, *me)
    # hatpehda.declare_triggers("human", *unctrl_triggers)

    # robot_goal = hatpehda.Goal("robot_goal")
    # robot_goal.isInContainer = {"cube_BGTG": ["throw_box_green"], "cube_GBTG": ["throw_box_green"]}

    hatpehda.set_state(robot_name, state_filled)
    hatpehda.add_tasks(robot_name, [("r_make_stack",)])

    human_state = deepcopy(state_filled)
    human_state.__name__ = "human_init"
    hatpehda.set_state(human_name, human_state)
    hatpehda.add_tasks(human_name, [("h_make_stack",)])

    sols = []
    fails = []
    start_explore = time.time()
    hatpehda.seek_plan_robot(hatpehda.agents, robot_name, sols, human_name, fails)
    end_explore = time.time()

    # gui.show_plan(sols, "robot", "human")
    # rosnode = ros.RosNode.start_ros_node("planner", lambda x: print("plop"))
    # time.sleep(5)
    # rosnode.send_plan(sols, "robot", "human")
    cost, root_action = hatpehda.select_conditional_plan(sols, robot_name, human_name, cost_dict)
    gui.show_plan(hatpehda.get_last_actions(root_action), robot_name, human_name, with_abstract=False)
    r_node.send_plan(hatpehda.get_last_actions(root_action), robot_name, human_name)


if __name__ == "__main__":
    regHandler = REGHandler()
    r_node = ros.RosNode.start_ros_node("planner", on_new_request = on_plan_request)
    r_node.wait_for_request()

    start = time.time()


    #print("policy cost", cost)

    #print("n mug: {}\texplore duration: {}sec\tselect duration: {}sec\tnumber of valid branches: {}".format(n_mug, end_explore - start_explore, end_select - start_select, len(sols)))

    # print(len(hatpehda.ma_solutions))
    # for ags in hatpehda.ma_solutions:
    #    print("Plan :", ags["robot"].global_plan, "with cost:", ags["robot"].global_plan_cost)
    # print("Took", end - start, "seconds")

    # regHandler.export_log("robot_planning")
    # regHandler.cleanup()

