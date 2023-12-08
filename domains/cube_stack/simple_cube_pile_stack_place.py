import pyhop
from pyhop.ros import RosNode

from copy import deepcopy

from typing import Dict

"""
Simple domain where a robot and a human have 3 different numbered cube each. They must build a 3 block height stack with 
a specific order. The order is such as the robot must place one cube, then the human and finally the robot again.
Result:


Plan : [('human_pick', 'cube1'), ('human_stack',), ('robot_pick', 'cube4'), ('robot_stack',), ('human_pick', 'cube2'), ('human_stack',)] with cost: 0.0
"""

### Operators definition

def human_pick(agents, self_state, self_name, c):
    if self_name in self_state.isReachableBy[c] and self_state.isCarrying[self_name] is None:
        for a in agents.values():
            a.state.isReachableBy[c] = []
            # should check if agent is in the same piece... Observability of action ?
            a.state.isCarrying[self_name] = c
        return agents
    else:
        return False


def robot_pick(agents: Dict[str, pyhop.Agent], self_state, self_name, c):
    if self_name in self_state.isReachableBy[c] and self_state.isCarrying[self_name] is None:
        for a in agents.values():
            a.state.isReachableBy[c] = []
            # should check if agent is in the same piece... Observability of action ?
            a.state.isCarrying[self_name] = c
        return agents
    else:
        return False


def human_stack(agents, self_state, self_name):
    if self_state.isCarrying[self_name] is not None:
        c = self_state.isCarrying[self_name]
        for a in agents.values():
            a.state.isOnStack[c] = True
            a.state.onStack.append(c)
            a.state.isCarrying[self_name] = None
        return agents
    else:
        return False

def human_wait(agents, self_state, self_name):
    return agents


def robot_stack(agents, self_state, self_name):
    if self_state.isCarrying[self_name] is not None:
        c = self_state.isCarrying[self_name]
        for a in agents.values():
            a.state.isOnStack[c] = True
            a.state.onStack.append(c)
            a.state.isCarrying[self_name] = None
        return agents
    else:
        return False


pyhop.declare_operators("human", human_pick, human_stack, human_wait)
pyhop.declare_operators("robot", robot_pick, robot_stack)

### Methods definitions

def moveb_m_human(agents, self_state, self_name, c, goal):
    if self_name in self_state.isReachableBy[c] and c in goal.isOnStack and goal.isOnStack[c] and not self_state.isOnStack[c]:
        return [("human_pick", c), ("human_stack",)]
    return []

def moveb_m_robot(agents, self_state: pyhop.State, self_name, c, goal):
    if self_name in self_state.isReachableBy[c] and c in goal.isOnStack and goal.isOnStack[c] and not self_state.isOnStack[c]:
            return [("robot_pick", c), ("robot_stack",)]
    return []

def stack_human(agents, self_state, self_name, goal):
    for c in self_state.cubes:
        if self_name in self_state.isReachableBy[c] and c in goal.isOnStack and goal.isOnStack[c] and not self_state.isOnStack[c]:
            if c == next(x for x in goal.onStack if x not in self_state.onStack and self_name in self_state.isReachableBy[x]):
                return [("move_one", c, goal), ("stack", goal)]
            else:
                return False
    return []

def wait_uncoop_human(agents, self_state, self_name, goal):
    for c in self_state.cubes:
        if self_name in self_state.isReachableBy[c] and c in goal.isOnStack and goal.isOnStack[c] and not self_state.isOnStack[c]:
            if c == next(x for x in goal.onStack if x not in self_state.onStack and self_name in self_state.isReachableBy[x]):
                return [("human_wait", ), ("stack", goal)]
            else:
                return False
    return []

def stack_robot(agents, self_state, self_name, goal):
    if goal.onStack == self_state.onStack:
        return []
    for c in self_state.cubes:
        if self_name in self_state.isReachableBy[c] and c in goal.isOnStack and goal.isOnStack[c] and not self_state.isOnStack[c]:
            if c == next(x for x in goal.onStack if x not in self_state.onStack and self_name in self_state.isReachableBy[x]):
                return [("move_one", c, goal), ("stack", goal)]
    return False


def make_stack_robot(agents, self_state, self_name, goal):
    if hasattr(goal, "stack_location") and goal.stack_location is not None:
        self_state.stack_location = goal.stack_location
    if not hasattr(self_state, "stack_location") or self_state.stack_location is None or self_state.stack_location == []:
        return False



pyhop.declare_methods("human", "move_one", moveb_m_human)
pyhop.declare_methods("robot", "move_one", moveb_m_robot)
pyhop.declare_methods("human", "stack", wait_uncoop_human, stack_human)
pyhop.declare_methods("robot", "stack", stack_robot)

pyhop.print_operators()

pyhop.print_methods()


def make_reachable_by(state, cubes, agent):
    if not hasattr(state, "isReachableBy"):
        state.isReachableBy = {}
    state.isReachableBy.update({c: agent for c in cubes})

def put_on_stack(state, cubes, is_stacked):
    if not hasattr(state, "isOnStack"):
        state.isOnStack = {}
    state.isOnStack.update({c: is_stacked for c in cubes})


state1_h = pyhop.State("state1_h")
state1_h.cubes = ["cube1", "cube2", "cube3", "cube4", "cube5", "cube6"]
make_reachable_by(state1_h, state1_h.cubes[:3], ["human"])
make_reachable_by(state1_h, state1_h.cubes[3:], ["robot"])
make_reachable_by(state1_h, state1_h.cubes[0:1], ["human", "robot"])
put_on_stack(state1_h, state1_h.cubes, False)
state1_h.isCarrying = {"human": None, "robot": None}
state1_h.onStack = []

state1_r = deepcopy(state1_h)

goal1_h = pyhop.Goal("goal1_h")
goal1_h.isOnStack = {"cube4": True, "cube1": True, "cube6": True}
goal1_h.onStack = ["cube4", "cube1", "cube6"]
goal1_r = deepcopy(goal1_h)

pyhop.set_state("human", state1_h)
pyhop.add_tasks("human", [('stack', goal1_h)])
pyhop.set_state("robot", state1_r)
pyhop.add_tasks("robot", [('stack', goal1_r)])

pyhop.print_state(pyhop.agents["human"].state)

sol = []
plans = pyhop.seek_plan_robot(pyhop.agents, "robot", sol)
rosnode = None

def on_new_plan_req(agents):
    pyhop.reset_agents_tasks()
    pyhop.set_state("robot", state1_r)
    pyhop.set_state("human", state1_h)
    for ag, tasks in agents.items():
        pyhop.add_tasks(ag, [(t[0], *t[1]) for t in tasks])

    pyhop.print_state(pyhop.agents["robot"].state)




    print(pyhop.agents["robot"].tasks)
    pyhop.print_methods("robot")
    pyhop.print_methods("human")
    sol = []
    plans = pyhop.seek_plan_robot(pyhop.agents, "robot", sol)
    print(sol)
    rosnode.send_plan(sol)

print(plans)

rosnode = RosNode.start_ros_node("planner", on_new_plan_req)
rosnode.wait_for_request()

print(len(sol), "solutions found")
from pyhop import gui
gui.show_plan(sol)
for agents in sol:
    reconstituted_plan = [None] * (2*len(agents["robot"].plan))
    reconstituted_plan[::2] = agents["robot"].plan
    reconstituted_plan[1::2] = agents["human"].plan
    for name, a in agents.items():
        print(name, "plan:", [("{} {}".format(o.why.id, o.why.name) if o.why is not None else None, o.name, *o.parameters) for o in a.plan])
    print("complete plan:", reconstituted_plan)

    print("######")


