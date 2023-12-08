#!/usr/bin/env python3

import hatpehda
from copy import deepcopy
from hatpehda import gui
#from hatpehda import ros



import time

### Helpers

def agent_plan_contains(plan, task_name):
    for p in plan:
        if p.name == task_name:
            return True
    return False

### Primitive tasks

def robot_get_water(agents, self_state, self_name):
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    for ag in agents.values():
       ag.state.isHolding[self_name] = ["water"]
    return agents

def robot_pour_water_in_machine(agents, self_state, self_name):
    if self_state.isHolding[self_name] is None or self_state.isHolding[self_name] == []:
        return False
    for ag in agents.values():
        ag.state.contains["coffee_machine"].append(ag.state.isHolding[self_name][0])
        ag.state.isHolding[self_name] = []
    return agents

def robot_pick_coffee(agents, self_state, self_name, closet):
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    if self_state.contains[closet] is None or self_state.contains[closet] == []:
        return False
    for ag in agents.values():
       ag.state.isHolding[self_name] = ["coffee"]
    return agents

def robot_put_coffee_in_machine(agents, self_state, self_name):
    if self_state.isHolding[self_name] is None or self_state.isHolding[self_name] == []:
        return False
    for ag in agents.values():
        ag.state.contains["coffee_machine"].append(ag.state.isHolding[self_name][0])
        ag.state.isHolding[self_name] = []
    return agents

def robot_ask_human_for_help(agents, self_state, self_name, human):
    hatpehda.add_tasks(human, [("human_help_make_coffee", self_name)], agents)
    return agents

def robot_serve_coffee(agents, _, __):
    return agents

def robot_update_human_inventory(agents, self_state, self_name, human, closet):
    agents[human].state.contains[closet] = self_state.contains[closet]
    return agents

def human_get_water(agents, self_state, self_name):
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    for ag in agents.values():
        ag.state.isHolding[self_name] = ["water"]
    return agents

def human_pour_water_in_machine(agents, self_state, self_name):
    if self_state.isHolding[self_name] is None or self_state.isHolding[self_name] == []:
        return False
    for ag in agents.values():
        ag.state.contains["coffee_machine"].append(ag.state.isHolding[self_name][0])
        ag.state.isHolding[self_name] = []
    return agents

def human_try_pick_coffee(agents, self_state, self_name, closet):
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    if agents["robot"].state.contains[closet] is None or agents["robot"].state.contains[closet] == []:
        self_state.contains[closet] = agents["robot"].state.contains[closet]
        return agents
    for ag in agents.values():
        ag.state.isHolding[self_name] = ["coffee"]
    return agents

def human_put_coffee_in_machine(agents, self_state, self_name):
    if self_state.isHolding[self_name] is None or self_state.isHolding[self_name] == []:
        return False
    for ag in agents.values():
        ag.state.contains["coffee_machine"].append(ag.state.isHolding[self_name][0])
        ag.state.isHolding[self_name] = []
    return agents


# As we don't know the agents name in advance, we store the operators here, until a ros plan call
ctrl_operators = [robot_get_water, robot_pour_water_in_machine, robot_pick_coffee, robot_put_coffee_in_machine,
                  robot_update_human_inventory, robot_ask_human_for_help, robot_serve_coffee]
unctrl_operators = [human_get_water, human_pour_water_in_machine, human_try_pick_coffee, human_put_coffee_in_machine]

#print(",\n".join(["\"{}\": 1.0".format(f.__name__) for f in ctrl_operators + unctrl_operators]))
cost_dict = {
    "robot_get_water": 1.0,
    "robot_pour_water_in_machine": 6.0,
    "robot_pick_coffee": 6.0,
    "robot_put_coffee_in_machine": 1.0,
    "robot_update_human_inventory": 0.1,
    "robot_ask_human_for_help": 1.0,
    "robot_serve_coffee": 1.0,
    "human_get_water": 1.0,
    "human_pour_water_in_machine": 1.0,
    "human_try_pick_coffee": 2.0,
    "human_put_coffee_in_machine": 1.0,
    "IDLE": 0.0
}

### Abstract Tasks

def robot_make_coffee_alone_i(agents, self_state, self_name):
    return [("robot_make_coffee_alone",)]

@hatpehda.multi_decomposition
def robot_make_coffee_alone(agents, self_state, self_name):
    return [[("robot_get_water",), ('robot_pour_water_in_machine',), ("robot_get_coffee", ), ("robot_put_coffee_in_machine", )],
            [("robot_get_coffee",), ("robot_put_coffee_in_machine",), ("robot_get_water",), ('robot_pour_water_in_machine',)]]

def robot_collaborate_make_coffee_no_comm_i(agents, self_state, self_name):
    return [("robot_collaborate_make_coffee_no_comm",)]

def robot_collaborate_make_coffee_no_comm(agents, self_state, self_name):
    return [("robot_ask_human_for_help", "human"), ("robot_help_make_coffee", "human")]

def robot_collaborate_make_coffee_with_belief_update_i(agents, self_state, self_name):
    return [("robot_collaborate_make_coffee_with_belief_update",)]

@hatpehda.multi_decomposition
def robot_collaborate_make_coffee_with_belief_update(agents, self_state, self_name):
    tasks = []
    for cupboard in self_state.individuals["Cupboard"]:
        if agents['human'].state.contains[cupboard] != self_state.contains[cupboard]:
            tasks.append([("robot_update_human_inventory", "human", cupboard), ("robot_ask_human_for_help", "human"), ("robot_help_make_coffee", "human")])
    if tasks == []:
        return False # Another decomposition handles it
    return tasks

@hatpehda.multi_decomposition
def robot_help_make_coffee(agents, self_state, self_name, human):
    if "water" in self_state.isHolding[human] and "coffee" not in self_state.contains["coffee_machine"]:
        return [[("robot_get_coffee",), ("robot_put_coffee_in_machine",)]]
    if agent_plan_contains(agents[human].plan, "human_try_pick_coffee") and "water" not in self_state.contains["coffee_machine"]:
        return [[("robot_get_water",), ("robot_pour_water_in_machine",)]]
    tasks = []
    if "coffee" not in self_state.contains["coffee_machine"]:
        tasks.append([("robot_get_coffee",), ("robot_put_coffee_in_machine",), ("robot_help_make_coffee", human)])
    if "water" not in self_state.contains["coffee_machine"]:
        tasks.append([("robot_get_water",), ("robot_pour_water_in_machine",), ("robot_help_make_coffee", human)])
    return tasks

def robot_get_coffee(agents, self_state, self_name):
    if "coffee" in self_state.isHolding[self_name]:
        return []
    min_cupboard = None
    min_dist = 999999.0
    for cupboard in self_state.individuals["Cupboard"]:
        if "coffee" in self_state.contains[cupboard] and self_state.distances[cupboard][0] < min_dist:
            min_dist = self_state.distances[cupboard][0]
            min_cupboard = cupboard
    if min_cupboard is None:
        return False
    return [("robot_pick_coffee", min_cupboard), ("robot_get_coffee", )]

@hatpehda.multi_decomposition
def human_help_make_coffee(agents, self_state, self_name, robot):
    if "water" in self_state.isHolding[robot] and "coffee" not in self_state.contains["coffee_machine"]:
        return [[("human_get_coffee",), ("human_put_coffee_in_machine",)]]
    if "coffee" in self_state.isHolding[robot] and "water" not in self_state.contains["coffee_machine"]:
        return [[("human_get_water",), ("human_pour_water_in_machine",)]]
    tasks = []
    if "coffee" not in self_state.contains["coffee_machine"]:
        tasks.append( [("human_get_coffee",), ("human_put_coffee_in_machine",), ("human_help_make_coffee", robot)])
    if "water" not in self_state.contains["coffee_machine"]:
        tasks.append([("human_get_water",), ("human_pour_water_in_machine",), ("human_help_make_coffee", robot)])
    return tasks


def human_get_coffee(agents, self_state, self_name):
    if "coffee" in self_state.isHolding[self_name]:
        return []
    min_cupboard = None
    min_dist = 999999.0
    for cupboard in self_state.individuals["Cupboard"]:
        if "coffee" in self_state.contains[cupboard] and self_state.distances[cupboard][0] < min_dist:
            min_dist = self_state.distances[cupboard][0]
            min_cupboard = cupboard
    if min_cupboard is None:
        return False
    return [("human_try_pick_coffee", min_cupboard), ("human_get_coffee",)]


# We don't know the agents name in advance so we store them here, until we can add the proper agents
# ctrl_methods = [("robot_make_coffee", robot_make_coffee_alone, robot_collaborate_make_coffee_no_comm, robot_collaborate_make_coffee_with_belief_update),
ctrl_methods = [("robot_make_coffee", robot_make_coffee_alone_i, robot_collaborate_make_coffee_no_comm_i, robot_collaborate_make_coffee_with_belief_update_i),
                ("robot_make_coffee_alone", robot_make_coffee_alone),
                ("robot_collaborate_make_coffee_no_comm", robot_collaborate_make_coffee_no_comm),
                ("robot_collaborate_make_coffee_with_belief_update", robot_collaborate_make_coffee_with_belief_update),
                ("robot_help_make_coffee", robot_help_make_coffee),
                ("robot_get_coffee", robot_get_coffee)]
unctrl_methods = [("human_help_make_coffee", human_help_make_coffee), ("human_get_coffee", human_get_coffee)]





if __name__ == "__main__":
    state = hatpehda.State("robot_init")
    state.types = {"Agent": ["isHolding"]}
    state.individuals = { "Cupboard": ["kitchen_cupboard", "pantry_cupboard"]}
    state.isHolding = {"human": [], "robot": []}
    state.contains = {"coffee_machine": [], "kitchen_cupboard": [], "pantry_cupboard": ["coffee"]}
    state.distances = {"kitchen_cupboard": [2.0], "pantry_cupboard": [4.0]}

    hatpehda.declare_operators("robot", *ctrl_operators)
    for me in ctrl_methods:
        hatpehda.declare_methods("robot", *me)
    hatpehda.declare_operators("human", *unctrl_operators)
    for me in unctrl_methods:
        hatpehda.declare_methods("human", *me)
    hatpehda.set_state("robot", state)
    hatpehda.add_tasks("robot", [("robot_make_coffee",), ("robot_serve_coffee",)])

    human_state = deepcopy(state)
    human_state.__name__ = "human_init"
    human_state.contains = {"coffee_machine": [], "kitchen_cupboard": ["coffee"], "pantry_cupboard": ["coffee"]}
    # Belief divergence: while the robot knows that kitchen_cupboard does not contain anything, the human thinks it is
    # containing coffee
    hatpehda.set_state("human", human_state)


    sols = []
    fails = []
    hatpehda.seek_plan_robot(hatpehda.agents, "robot", sols, "human", fails)
    end = time.time()

    print(len(sols))

    gui.show_plan(sols, "robot", "human", with_abstract=True)
    #rosnode = ros.RosNode.start_ros_node("planner", lambda x: print("plop"))
    #time.sleep(5)
    #rosnode.send_plan(sols, "robot", "human")
    input()
    cost, plan_root = hatpehda.select_conditional_plan(sols, "robot", "human", cost_dict)

    gui.show_plan(hatpehda.get_last_actions(plan_root), "robot", "human", with_abstract=True)
    #n.send_plan(hatpehda.get_last_actions(plan_root), "robot", "human")
    print("policy cost", cost)

    # print(len(hatpehda.ma_solutions))
    # for ags in hatpehda.ma_solutions:
    #    print("Plan :", ags["robot"].global_plan, "with cost:", ags["robot"].global_plan_cost)
    # print("Took", end - start, "seconds")

    # regHandler.export_log("robot_planning")
    # regHandler.cleanup()
