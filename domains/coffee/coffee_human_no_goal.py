import hatpehda
from copy import deepcopy

from typing import Dict


"""
This example depicts a two rooms place, kitchen and experimentation room. The robot start at the experimentation room
with the task to get a coffee. The coffee machine is in the kitchen. The robot knows that a human with no task to do is 
in the kitchen. The robot can give a goal to the human and handover object to and from the human.

Result:
Plan : [('robot_pick_mug', 'mug1'), ('robot_navigate', 'kitchen'), ('robot_ask_to_human_do_task', 'human', ('human_get_mug_make_coffee', <hatpehda.Goal object at 0x7f52550179e8>, 'robot', 'mug1')), ('robot_handover_give', 'human'), ('human_handover_take', 'robot'), ('human_make_coffee', 'mug1'), ('human_handover_give', 'robot'), ('robot_handover_end',), ('robot_handover_take', 'human'), ('robot_navigate', 'experimentation_room'), ('human_handover_end',)] with cost: 0.0

"""

### Helpers

def agentsInSameRoomAs(state, agent_name, agents):
    currentRoom = state.currentLocation[agent_name]
    ags = [agents[a] for a in state.agentsInRoom[currentRoom]]
    return ags

### Operators definition

def robot_pick_mug(agents: Dict[str, hatpehda.Agent], self_state, self_name, m):
    if self_name in self_state.isReachableBy[m] and self_state.isCarrying[self_name] is None:
        for a in agentsInSameRoomAs(self_state, self_name, agents):
            a.state.isReachableBy[m] = []
            a.state.isCarrying[self_name] = m
        return agents
    else:
        return False


def robot_navigate(agents: Dict[str, hatpehda.Agent], self_state, self_name, to_loc):
    from_loc = self_state.currentLocation[self_name]
    if to_loc in self_state.connectedTo[from_loc]:
        # Updating beliefs of the agents in the room we just left
        for a in agentsInSameRoomAs(self_state, self_name, agents):
            a.state.currentLocation[self_name] = to_loc
            a.state.agentsInRoom[from_loc].remove(self_name)
            a.state.agentsInRoom[to_loc].append(self_name)
        # Updating beliefs of the agents in the room we arrive in
        for a in agentsInSameRoomAs(self_state, self_name, agents):
            a.state.currentLocation[self_name] = to_loc
            if self_name in a.state.agentsInRoom[from_loc]: a.state.agentsInRoom[from_loc].remove(self_name)  # Agents in the room we enter may not be aware we were in the room we just left
            a.state.agentsInRoom[to_loc].append(self_name)

            # Now update observable things about the robot
            a.state.isCarrying[self_name] = self_state.isCarrying[self_name]

            # We also should update what is the new room... But we potentially do not know so... replan ?

        return agents
    else:
        return False


def robot_ask_to_human_do_task(agents: Dict[str, hatpehda.Agent], self_state, self_name, human, task):
    if self_state.currentLocation[self_name] == self_state.currentLocation[human]:
        # We should also check if task and paramaters are verbalizable (REG)
        agents[human].tasks.insert(0, task)  # The human will accept...
        return agents
    else:
        return False
    
def robot_handover_give(agents: Dict[str, hatpehda.Agent], self_state, self_name, agent):
    if self_state.isCarrying[self_name] is not None and self_state.currentLocation[self_name] == self_state.currentLocation[agent]:
        return agents
    else:
        return False

def robot_handover_end(agents: Dict[str, hatpehda.Agent], self_state, self_name):
    if self_state.isCarrying[self_name] is None:
        return agents
    else:
        return False

def robot_handover_take(agents: Dict[str, hatpehda.Agent], self_state, self_name, agent):
    if self_state.isCarrying[self_name] is None and "handover_give" in agents[agent].plan[-1][0] and agents[agent].plan[-1][1] == self_name:
        obj = self_state.isCarrying[agent]
        for a in agentsInSameRoomAs(self_state, self_name, agents):
            a.state.isReachableBy[obj] = []
            a.state.isCarrying[self_name] = obj
            a.state.isCarrying[agent] = None
        return agents
    else:
        return False

def robot_wait(agents, self_state, self_name):
    return agents

def human_handover_give(agents: Dict[str, hatpehda.Agent], self_state, self_name, agent):
    if self_state.isCarrying[self_name] is not None and self_state.currentLocation[self_name] == self_state.currentLocation[agent]:
        return agents
    else:
        return False
        
def human_handover_end(agents: Dict[str, hatpehda.Agent], self_state, self_name):
    if self_state.isCarrying[self_name] is None:
        return agents
    else:
        return False
    
def human_handover_take(agents: Dict[str, hatpehda.Agent], self_state, self_name, agent):
    if self_state.isCarrying[self_name] is None and "handover_give" in agents[agent].plan[-1][0] and agents[agent].plan[-1][1] == self_name:
        obj = self_state.isCarrying[agent]
        for a in agentsInSameRoomAs(self_state, self_name, agents):
            a.state.isReachableBy[obj] = []
            a.state.isCarrying[self_name] = obj
            a.state.isCarrying[agent] = None
        return agents
    else:
        return False

def human_make_coffee(agents: Dict[str, hatpehda.Agent], self_state, self_name, mug):
    if self_state.isCarrying[self_name] == mug:
        if self_state.contains[mug] == "coffee":
            return agents
        elif self_state.contains[mug] is None:
            for a in agentsInSameRoomAs(self_state, self_name, agents):
                a.state.contains[mug] = "coffee"
            return agents
        else:
            return False
    else:
        return False


hatpehda.declare_operators("human", human_handover_give, human_handover_end, human_handover_take, human_make_coffee)
hatpehda.declare_operators("robot", robot_pick_mug, robot_navigate, robot_ask_to_human_do_task, robot_handover_give,
                           robot_handover_end, robot_handover_take, robot_wait)

### Methods definitions

def robot_get_coffee(agents, self_state, self_name, goal, mug):
    coffee_machine_loc = self_state.isIn["coffee_machine"]
    if self_state.contains[mug] == "coffee":
        return []
    human = next(a for a in self_state.agentsInRoom[coffee_machine_loc] if "human" in a)
    if "human" not in self_state.agentsInRoom[coffee_machine_loc]:
        return False
    if self_state.currentLocation[self_name] == coffee_machine_loc:
        return [("robot_pick_mug", mug), ("robot_ask_to_fill_cup", goal, mug, human)]
    else:
        return [("robot_pick_mug", mug), ("robot_navigate", coffee_machine_loc),
                ("robot_ask_to_fill_cup", goal, mug, human), ("robot_navigate", self_state.currentLocation[self_name])]

def robot_ask_to_fill_cup(agents, self_state, self_name, goal, mug, human):
    return [("robot_ask_to_human_do_task", human, ("human_get_mug_make_coffee", goal, self_name, mug)),
            ("robot_handover_give", human), ("robot_handover_end",), ("robot_wait_for_human", human), ("robot_handover_take", human)]

def robot_wait_for_human(agents, self_state, self_name, human):
    print(agents[human].plan)
    if agents[human].plan[-1][0] != "human_handover_give":
        return [("robot_wait",), ("robot_wait_for_human", human)]
    else:
        return []

def human_get_mug_make_coffee(agents, self_state, self_name, goal, giver, mug):
    return [("human_handover_take", giver), ("human_make_coffee", mug), ("human_handover_give", giver), ("human_handover_end",)]




hatpehda.declare_methods("human", "human_get_mug_make_coffee", human_get_mug_make_coffee)
hatpehda.declare_methods("robot", "robot_get_coffee", robot_get_coffee)
hatpehda.declare_methods("robot", "robot_ask_to_fill_cup", robot_ask_to_fill_cup)
hatpehda.declare_methods("robot", "robot_wait_for_human", robot_wait_for_human)

hatpehda.print_operators()

hatpehda.print_methods()


state1_r = hatpehda.State("state1_r")
state1_r.isIn = {"coffee_machine": "kitchen", "mug1": "experimentation_room", "mug2": "experimentation_room", "mug3": "kitchen"}
state1_r.contains = {"mug1": None, "mug2": "water", "mug3": None}
state1_r.agentsInRoom = {"kitchen": ["human"], "experimentation_room": ["robot"]}
state1_r.currentLocation = {"robot": "experimentation_room", "human": "kitchen"}
state1_r.isReachableBy = {"mug1": ["robot"], "mug2": ["robot"], "mug3": ["human"]}
state1_r.isCarrying = {"robot": None, "human": None}
state1_r.connectedTo = {"kitchen": ["experimentation_room"], "experimentation_room": ["kitchen"]}


state1_h = deepcopy(state1_r)

goal1_r = hatpehda.Goal("goal1_r")
goal1_h = deepcopy(goal1_r)

hatpehda.set_state("human", state1_h)
hatpehda.set_state("robot", state1_r)
hatpehda.add_tasks("robot", [("robot_get_coffee", goal1_r, "mug1")])

hatpehda.print_state(hatpehda.agents["robot"].state)

# plans = hatpehda.multi_agent_planning(verbose=0)
#
# for ags in hatpehda.ma_solutions:
#     print("Plan :", ags["robot"].global_plan, "with cost:", ags["robot"].global_plan_cost)
#
# print(plans)

sol = []
plans = hatpehda.seek_plan_robot(hatpehda.agents, "robot", sol)

print(plans)

print(len(sol), "solutions found")
for agents in sol:
    reconstituted_plan = [None] * (2*len(agents["robot"].plan))
    reconstituted_plan[::2] = agents["robot"].plan
    reconstituted_plan[1::2] = agents["human"].plan
    for name, a in agents.items():
        print(name, "plan:", a.plan)
    print("complete plan:", reconstituted_plan)

    print("######")
