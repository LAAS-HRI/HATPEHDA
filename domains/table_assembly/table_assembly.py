import hatpehda
from copy import deepcopy
from hatpehda import gui

from typing import Dict

def same_last_tasks(plan, n, task=None):
    if len(plan) < n:
        return False
    last_tasks = [plan[-i].name for i in range(1, n + 1)]
    if task is not None and last_tasks[0] != task:
        return False
    return last_tasks.count(last_tasks[0]) == len(last_tasks)

### Operators definition

def human_pick(agents, self_state, self_name, p):
    if self_name in self_state.isReachableBy[p] and self_state.isCarrying[self_name] == []:
        for a in agents.values():
            a.state.isReachableBy[p] = []
            # should check if agent is in the same piece... Observability of action ?
            a.state.isCarrying[self_name] = [p]
        return agents
    else:
        return False


def robot_pick(agents: Dict[str, hatpehda.Agent], self_state, self_name, c):
    if self_name in self_state.isReachableBy[c] and self_state.isCarrying[self_name] == []:
        for a in agents.values():
            a.state.isReachableBy[c] = []
            # should check if agent is in the same piece... Observability of action ?
            a.state.isCarrying[self_name] = [c]
        return agents
    else:
        return False


def human_assemble(agents, self_state, self_name, top):
    if self_state.isCarrying[self_name] == [] and len(self_state.assembly[top]) < 4:
        c = self_state.isCarrying[self_name][0]
        for a in agents.values():
            a.state.assembly[top].append(c)
            a.state.isCarrying[self_name] = []
        return agents
    else:
        return False


def robot_assemble(agents, self_state, self_name, top):
    if self_state.isCarrying[self_name] != [] and len(self_state.assembly[top]) < 4:
        c = self_state.isCarrying[self_name][0]
        for a in agents.values():
            a.state.assembly[top].append(c)
            a.state.isCarrying[self_name] = []
        return agents
    else:
        return False

def robot_ask_human_to_give_leg(agents, self_state, self_name, human, leg):
    hatpehda.add_tasks(human, [("take_give_to_robot", leg, self_name)], agents)
    print(agents[human].tasks)
    return agents

def robot_ask_to_help_in_assembly(agents, self_state, self_name, human, top, legs):
    goal = hatpehda.Goal("human_goal")
    goal.assembly = {top: legs}
    hatpehda.add_tasks(human, [("assemble_table", top, goal)], agents)
    return agents

def human_give_to_robot(agents, self_state, self_name, robot):
    if self_state.isCarrying[self_name] != []:
        return agents
    return False

def human_wait_for_give(agents, self_state, self_name, robot):
    return agents

def robot_wait_for_take(agents, self_state, self_name, human):
    return agents

def robot_take_from_human(agents, self_state, self_name, human):
    if self_state.isCarrying[self_name] == [] and self_state.isCarrying[human] != []:
        if agents[human].plan[-1].name == "human_give_to_robot" or agents[human].plan[-1].name == "human_wait_for_give":
            for a in agents.values():
                a.state.isCarrying[self_name] = a.state.isCarrying[human]
                a.state.isCarrying[human] = []
            return agents
    return False


hatpehda.declare_operators("human", human_pick, human_assemble, human_give_to_robot, human_wait_for_give)
hatpehda.declare_operators("robot", robot_pick, robot_assemble, robot_ask_human_to_give_leg, robot_ask_to_help_in_assembly,
                           robot_take_from_human, robot_wait_for_take)

### Methods definitions

def assemble_tables_human(agents, self_state, self_name, goal):
    for top in goal.assembly:
        return [("assemble_table", top, goal)]

def assemble_table_human(agents, self_state, self_name, top, goal):
    for leg in goal.assembly[top]:
        if leg not in self_state.assembly[top]:
            return [("handle_leg", leg, top), ("assemble_table", top, goal)]

def take_give_leg_human(agents, self_state, self_name, leg, top):
    robot = "robot"
    return [("take_give_to_robot", leg, robot)]

def take_assemble_human(agents, self_state, self_name, leg, top):
    return [("human_pick", leg), ("human_assemble", top)]

def take_give_leg_to_robot_human(agents, self_state, self_name, leg, robot):
    return [("human_pick", leg), ("give_to_robot", robot)]

def handover_give_human(agents, self_state, self_name, robot):
    if self_state.isCarrying[self_name] == []:
        return []
    if agents[self_name].plan[-1].name != "human_give_to_robot" or agents[self_name].plan[-1].name != "human_wait_for_give":
        return [("human_give_to_robot", robot), ("give_to_robot", robot)]
    elif agents[robot].plan[-1].name == "robot_take_from_human" and agents[robot].plan[-1].parameters[0] == self_name:
        return []
    elif same_last_tasks(agents[self_name].plan, 3, "human_wait_for_give"):
        return False
    else:
        return [("human_wait_for_give", robot), ("give_to_robot", robot)]

def assemble_tables_robot(agents, self_state, self_name, goal):
    for top in goal.assembly:
        if len(self_state.assembly[top]) < 4:
            return [("assemble_table", top, goal)]

def assemble_tables_with_help_robot(agents, self_state, self_name, goal):
    human = "human"
    for top in goal.assembly:
        if len(self_state.assembly[top]) < 4:
            return [("robot_ask_to_help_in_assembly", human, top, goal.assembly[top]), ("assemble_table", top, goal)]

def assemble_table_robot(agents, self_state, self_name, top, goal):
    for leg in goal.assembly[top]:
        if leg not in self_state.assembly[top]:
            return [("handle_leg", leg, top), ("assemble_table", top, goal)]
    return []


def handover_assemble_robot(agents, self_state, self_name, leg, top):
    for ag in agents:
        if leg in self_state.isCarrying[ag]:
            if agents[self_name].plan[-1].name == "human_give_to_robot" or agents[self_name].plan[-1].name == "human_wait_for_give":
                return [("robot_take_from_human", ag), ("robot_assemble", top)]
    for ag in agents:
        if agents[ag].tasks is None or len(agents[ag].tasks) == 0:
            return [("robot_ask_human_to_give_leg", ag, leg), ("handover_take", ag), ("robot_assemble", top)]
    return False


def take_assemble_robot(agents, self_state, self_name, leg, top):
    if leg in self_state.canReach[self_name]:
        return [("robot_pick", leg), ("robot_assemble", top)]
    else:
        return False

def handover_take_robot(agents, self_state, self_name, human):
    if agents[human].plan[-1].name == "human_give_to_robot" or agents[human].plan[-1].name == "human_wait_for_give":
        return [("robot_take_from_human", human)]
    elif same_last_tasks(agents[self_name].plan, 3, "robot_wait_for_take"):
        return False
    else:
        return [("robot_wait_for_take", human), ("handover_take", human)]






hatpehda.declare_methods("human", "assemble_table", assemble_table_human)
hatpehda.declare_methods("human", "handle_leg", take_give_leg_human, take_assemble_human)
hatpehda.declare_methods("human", "take_give_to_robot", take_give_leg_to_robot_human)
hatpehda.declare_methods("human", "give_to_robot", handover_give_human)
hatpehda.declare_methods("robot", "assemble_tables", assemble_tables_robot, assemble_tables_with_help_robot)
hatpehda.declare_methods("robot", "assemble_table", assemble_table_robot)
hatpehda.declare_methods("robot", "handle_leg", handover_assemble_robot, take_assemble_robot)
hatpehda.declare_methods("robot", "handover_take", handover_take_robot)


hatpehda.print_operators()

hatpehda.print_methods()


def make_reachable_by(state, indivs, agents):
    if not hasattr(state, "isReachableBy"):
        state.isReachableBy = {}
    if not hasattr(state, "canReach"):
        state.canReach = {}
    for c in indivs:
        if c not in state.isReachableBy:
            state.isReachableBy[c] = []
        for ag in agents:
            if ag not in state.canReach:
                state.canReach[ag] = []
            state.isReachableBy[c].append(ag)
            state.canReach[ag].append(c)



state1_r = hatpehda.State("state1_r")
state1_r.individuals = {"leg": ["leg1", "leg2", "leg3", "leg4"], "top": ["top1"]}
make_reachable_by(state1_r, state1_r.individuals["leg"], ["human"])
make_reachable_by(state1_r, ["leg3", "leg4"], ["robot"])
state1_r.isCarrying = {"human": [], "robot": []}
state1_r.assembly = {"top1": []}

state1_h = deepcopy(state1_r)

goal1_r = hatpehda.Goal("goal1_r")
goal1_r.assembly = {"top1": ["leg1", "leg2", "leg3", "leg4"]}
#goal1_h = deepcopy(goal1_r)

hatpehda.set_state("human", state1_h)
#hatpehda.add_tasks("human", [('stack', goal1_h)])
hatpehda.set_state("robot", state1_r)
hatpehda.add_tasks("robot", [('assemble_tables', goal1_r)])

#hatpehda.print_state(hatpehda.agents["human"].state)

sol = []
fails = []
plans = hatpehda.seek_plan_robot(hatpehda.agents, "robot", sol, uncontrollable_agent_name="human", fails=fails)

gui.show_plan(sol + fails, "robot", "human")


print(fails)

print(len(sol), "solutions found")
for agents in sol:
    for name, a in agents.items():
        print(name, "plan:", a.plan)
    print("######")


