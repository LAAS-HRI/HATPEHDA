import hatpehda
from copy import deepcopy

from typing import Dict

"""
Simple domain where a robot and a human have 3 different numbered cube each. They must build a 3 block height stack with 
a specific order. The order is such as the robot must place one cube, then the human and finally the robot again.
However, each 3 actions (from either the robot or the human) a red light goes on. When the red light is on neither
the robot nor the human can act. The only action possible is for the human to turn off this red light allowing to
continue the task.
Result :
Plan : [('human_pick', 'cube1'), ('human_stack',), ('robot_pick', 'cube4'), ('switch_off',), ('robot_stack',), ('human_pick', 'cube2'), ('human_stack',), ('switch_off',)] with cost: 0.0
"""

### Helper
def check_redlight(state):
    state.redLightCounter += 1
    if state.redLightCounter >= 3:
        state.redLightOn = True

### Operators definition

def human_pick(agents, self_state, self_name, c):
    if self_state.redLightOn:
        return False
    if self_name in self_state.isReachableBy[c] and self_state.isCarrying[self_name] is None:
        for a in agents.values():
            a.state.isReachableBy[c] = []
            # should check if agent is in the same piece... Observability of action ?
            a.state.isCarrying[self_name] = c
            check_redlight(a.state)
        return agents
    else:
        return False


def robot_pick(agents: Dict[str, hatpehda.Agent], self_state, self_name, c):
    if self_state.redLightOn:
        return False
    if self_name in self_state.isReachableBy[c] and self_state.isCarrying[self_name] is None:
        for a in agents.values():
            a.state.isReachableBy[c] = []
            # should check if agent is in the same piece... Observability of action ?
            a.state.isCarrying[self_name] = c
            check_redlight(a.state)
        return agents
    else:
        return False


def human_stack(agents, self_state, self_name):
    if self_state.redLightOn:
        return False
    if self_state.isCarrying[self_name] is not None:
        c = self_state.isCarrying[self_name]
        for a in agents.values():
            a.state.isOnStack[c] = True
            a.state.onStack.append(c)
            a.state.isCarrying[self_name] = None
            check_redlight(a.state)
        return agents
    else:
        return False


def robot_stack(agents, self_state, self_name):
    if self_state.redLightOn:
        return False
    if self_state.isCarrying[self_name] is not None:
        c = self_state.isCarrying[self_name]
        for a in agents.values():
            a.state.isOnStack[c] = True
            a.state.onStack.append(c)
            a.state.isCarrying[self_name] = None
            check_redlight(a.state)
        return agents
    else:
        return False

def switch_off_while_holding(agents, self_state, self_name):
    if self_state.redLightOn and self_state.isCarrying[self_name] is not None:
        for a in agents.values():
            a.state.redLightCounter = 0
            a.state.redLightOn = False
        return agents
    else:
        return False

def switch_off(agents, self_state, self_name):
    if self_state.redLightOn and self_state.isCarrying[self_name] is None:
        for a in agents.values():
            a.state.redLightCounter = 0
            a.state.redLightOn = False
        return agents
    else:
        return False


hatpehda.declare_operators("human", human_pick, human_stack, switch_off_while_holding, switch_off)
hatpehda.declare_operators("robot", robot_pick, robot_stack)

### Methods definitions

def moveb_m_human(agents, self_state, self_name, c, goal):
    """
    This method implements the following block-stacking algorithm:
    If there's a block that can be moved to its final position, then
    do so and call move_blocks recursively. Otherwise, if there's a
    block that needs to be moved and can be moved to the table, then
    do so and call move_blocks recursively. Otherwise, no blocks need
    to be moved.
    """
    if self_name in self_state.isReachableBy[c] and c in goal.isOnStack and goal.isOnStack[c] and not self_state.isOnStack[c]:
        return [("human_pick", c), ("human_stack",)]
    return []

def moveb_m_robot(agents, self_state: hatpehda.State, self_name, c, goal):
    """
    This method implements the following block-stacking algorithm:
    If there's a block that can be moved to its final position, then
    do so and call move_blocks recursively. Otherwise, if there's a
    block that needs to be moved and can be moved to the table, then
    do so and call move_blocks recursively. Otherwise, no blocks need
    to be moved.
    """
    if self_name in self_state.isReachableBy[c] and c in goal.isOnStack and goal.isOnStack[c] and not self_state.isOnStack[c]:
            return [("robot_pick", c), ("robot_stack",)]
    return []

def stack_human(agents, self_state, self_name, goal):
    for c in self_state.cubes:
        if self_name in self_state.isReachableBy[c] and c in goal.isOnStack and goal.isOnStack[c] and not self_state.isOnStack[c]:
            if c == next(x for x in goal.onStack if x not in self_state.onStack):
                return [("move_one", c, goal), ("stack", goal)]
            else:
                return False
    return []

def stack_robot(agents, self_state, self_name, goal):
    for c in self_state.cubes:
        if self_name in self_state.isReachableBy[c] and c in goal.isOnStack and goal.isOnStack[c] and not self_state.isOnStack[c]:
            if c == next(x for x in goal.onStack if x not in self_state.onStack):
                return [("move_one", c, goal), ("stack", goal)]
            else:
                return False
    return []

def switch_light_off_human(agents, self_state, self_name):
    if self_state.redLightOn:
        if self_state.isCarrying[self_name] is not None:
            return [("switch_off_while_holding",)]
        else:
            return [("switch_off",)]
    else:
        return []

hatpehda.declare_methods("human", "move_one", moveb_m_human)
hatpehda.declare_methods("robot", "move_one", moveb_m_robot)
hatpehda.declare_methods("human", "stack", stack_human)
hatpehda.declare_methods("robot", "stack", stack_robot)
hatpehda.declare_methods("human", "switch_light_off", switch_light_off_human)

### Triggers

def on_red_light(agents, self_state, self_name):
    if self_state.redLightOn:
        return [("switch_light_off",)]
    return False

hatpehda.declare_trigger("human", on_red_light)

hatpehda.print_operators()

hatpehda.print_methods()


def make_reachable_by(state, cubes, agent):
    if not hasattr(state, "isReachableBy"):
        state.isReachableBy = {}
    state.isReachableBy.update({c: agent for c in cubes})

def put_on_stack(state, cubes, is_stacked):
    if not hasattr(state, "isOnStack"):
        state.isOnStack = {}
    state.isOnStack.update({c: is_stacked for c in cubes})


state1_h = hatpehda.State("state1_h")
state1_h.cubes = ["cube1", "cube2", "cube3", "cube4", "cube5", "cube6"]
make_reachable_by(state1_h, state1_h.cubes[:3], ["human"])
make_reachable_by(state1_h, state1_h.cubes[3:], ["robot"])
put_on_stack(state1_h, state1_h.cubes, False)
state1_h.isCarrying = {"human": None, "robot": None}
state1_h.onStack = []
state1_h.redLightOn = False
state1_h.redLightCounter = 0

state1_r = deepcopy(state1_h)

goal1_h = hatpehda.Goal("goal1_h")
goal1_h.isOnStack = {"cube1": True, "cube2": True, "cube4": True}
goal1_h.onStack = ["cube1", "cube4", "cube2"]
goal1_r = deepcopy(goal1_h)

hatpehda.set_state("human", state1_h)
hatpehda.add_tasks("human", [('stack', goal1_h)])
hatpehda.set_state("robot", state1_r)
hatpehda.add_tasks("robot", [('stack', goal1_r)])

hatpehda.print_state(hatpehda.agents["human"].state)

plans = hatpehda.multi_agent_planning(verbose=2)

for ags in hatpehda.ma_solutions:
    print("Plan :", ags["robot"].global_plan, "with cost:", ags["robot"].global_plan_cost)

print(plans)


