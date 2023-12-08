"""
HATPEHDA, version 1.0.0 -- an HTN planner emulating human decisions and actions written in Python, inspired from PyHop (under Apache 2.0 License)
Author: Guilhem Buisan

Copyright 2020 Guilhem Buisan

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import print_function

import copy
import sys
from collections import namedtuple
from enum import Enum
from typing import Dict

############################################################
# States and goals
class HumanPredictionType(Enum):
    FIRST_APPLICABLE_ACTION = 0
    ALL_APPLICABLE_ACTIONS = 1

human_prediction_type = HumanPredictionType.ALL_APPLICABLE_ACTIONS

Plan = namedtuple("Plan", ["plan", "cost"])

class Task():
    __ID = 0
    def __init__(self, name, parameters, why, decompo_number, agent):
        self.id = Task.__ID
        Task.__ID += 1
        self.name = name
        self.parameters = parameters
        self.agent = agent
        self.why = why  # From which task it is decomposed
        self.decompo_number = decompo_number  # The number of the decomposition from the abstract task (self.why)
        self.applicable = True
        self.previous = None
        self.next = []

    def assign_next_id(self):
        self.id = Task.__ID
        Task.__ID += 1

class Operator(Task):
    def __init__(self, name, parameters, agent, why, decompo_number, function):
        super().__init__(name, parameters, why, decompo_number, agent)
        self.function = function
        self.cost = 0.0

    @staticmethod
    def copy_new_id(other):
        new = copy.deepcopy(other)
        new.assign_next_id()
        return new

    def __repr__(self):
        return str((self.id, self.name, *self.parameters))

class AbstractTask(Task):
    def __init__(self, name, parameters, agent, why, decompo_number, how, number_of_decompo):
        super().__init__(name, parameters, why, decompo_number, agent)
        self.how = how  # List of task networks this task has been decomposed into (after each decompo function has been called)
        self.number_of_decompo = number_of_decompo  # How many decomposition this task has (maybe not successful ones)

class State():
    """A state is just a collection of variable bindings."""

    def __init__(self, name):
        self.__name__ = name
        self.__static_props__ = []
        self.__dynamic_props__ = []

    def set_static_props(self, static_props):
        self.__static_props__ = static_props
    
    def set_dynamic_props(self, dynamic_props):
        self.__dynamic_props__ = dynamic_props

class Goal():
    """A goal is just a collection of variable bindings."""

    def __init__(self, name):
        self.__name__ = name


### print_state and print_goal are identical except for the name
def print_state(state, indent=4):
    """Print each variable in state, indented by indent spaces."""
    if state != False:
        for (name, val) in vars(state).items():
            if state.__dynamic_props__==[] and name!='__name__' and name!='__static_props__' and name!='__dynamic_props__' or name in state.__dynamic_props__:
                for x in range(indent): sys.stdout.write(' ')
                sys.stdout.write(state.__name__ + '.' + name)
                print(' =', val)
    else:
        print('False')

def print_goal(goal, indent=4):
    """Print each variable in goal, indented by indent spaces."""
    if goal != False:
        for (name, val) in vars(goal).items():
            if name != '__name__':
                for x in range(indent): sys.stdout.write(' ')
                sys.stdout.write(goal.__name__ + '.' + name)
                print(' =', val)
    else:
        print('False')


############################################################
# Helper functions that may be useful in domain models
def forall(seq, cond):
    """True if cond(x) holds for all x in seq, otherwise False."""
    for x in seq:
        if not cond(x): return False
    return True

def find_if(cond, seq):
    """
    Return the first x in seq such that cond(x) holds, if there is one.
    Otherwise return None.
    """
    for x in seq:
        if cond(x): return x
    return None


############################################################
# Commands to tell Pyhop what the operators and methods are
class Agent:
    def __init__(self, name):
        self.name = name
        self.operators = {} # type: Dict[str, function]
        self.methods = {} # type: Dict[str, function]
        self.state = None
        self.goal = None
        self.tasks = []
        self.plan = []
        self.triggers = []

agents = {}  # type: Dict[str, Agent]

def declare_operators(agent, *op_list):
    """
    Call this after defining the operators, to tell Pyhop what they are.
    op_list must be a list of functions, not strings.
    """
    if agent not in agents:
        agents[agent] = Agent(agent)

    agents[agent].operators.update({op.__name__: op for op in op_list})
    return agents

def declare_methods(agent, task_name, *method_list):
    """
    Call this once for each task, to tell Pyhop what the methods are.
    task_name must be a string.
    method_list must be a list of functions, not strings.
    """
    if agent not in agents:
        agents[agent] = Agent(agent)
    agents[agent].methods.update({task_name: list(method_list)})
    return agents

def set_state(agent, state):
    if agent not in agents:
        agents[agent] = Agent(agent)
    agents[agent].state = state

def set_goal(agent, goal):
    if agent not in agents:
        agents[agent] = Agent(agent)
    agents[agent].goal = goal

def add_tasks(agent, tasks, to_agents=None):
    if to_agents is None:
        to_agents = agents
    if agent not in to_agents:
        to_agents[agent] = Agent(agent)
    for t in tasks:
        if t[0] in to_agents[agent].operators:
            to_agents[agent].tasks.append(Operator(t[0], t[1:], agent, None, None, to_agents[agent].operators[t[0]]))
        elif t[0] in to_agents[agent].methods:
            to_agents[agent].tasks.append(AbstractTask(t[0], t[1:], agent, None, None, [], len(to_agents[agent].methods[t[0]])))
        else:
            raise TypeError("Asked to add task '{}' to agent '{}' but it is not defined "
                            "neither in its operators nor methods.".format(t[0], agent))

def declare_triggers(agent, *triggers):
    if agent not in agents:
        agents[agent] = Agent(agent)
    agents[agent].triggers += triggers

def reset_agents_tasks():
    for agent in agents:
        agents[agent].tasks = []

def reset_planner():
    global agents
    agents = {}


############################################################
# Decorators for specific operators and methods functions
def multi_decomposition(decompo):
    def prepending(*args, **kwargs):
        result = decompo(*args, **kwargs)
        if result is False or result == [] or result is None:
            return result
        return "MULTI", result
    return prepending


############################################################
# Commands to find out what the operators and methods are
def print_operators(agent=None):
    """Print out the names of the operators"""
    if agent is None:
        print("==OPERATORS==")
        for a, ag in agents.items():
            print("Agent:", a)
            print("\t", ', '.join(ag.operators))
    else:
        print('OPERATORS:', ', '.join(agents[agent].operators))

def print_methods(agent=None):
    """Print out a table of what the methods are for each task"""
    print("==METHODS==")
    print('\t{:<14}{}'.format('TASK:', 'METHODS:'))
    if agent is None:
        for a, ag in agents.items():
            print("Agent:", a)
            for task in ag.methods:
                print('\t{:<14}'.format(task) + ', '.join([f.__name__ for f in ag.methods[task]]))
    else:
        ag = agents[agent]
        for task in ag.methods:
            print('\t{:<14}'.format(task) + ', '.join([f.__name__ for f in ag.methods[task]]))


############################################################
# Cost related functions
def default_cost_idle_function():
    return 0.0
def set_idle_cost_function(idle_function):
    global idle_cost_function
    idle_cost_function = idle_function
idle_cost_function = default_cost_idle_function

def default_cost_wait_function():
    return 0.0
def set_wait_cost_function(wait_function):
    global wait_cost_function
    wait_cost_function = wait_function
wait_cost_function = default_cost_wait_function

def set_undesired_state_functions(functions):
    global undesired_state_functions
    undesired_state_functions = functions
undesired_state_functions = []

def set_undesired_sequence_functions(functions):
    global undesired_sequence_functions
    undesired_sequence_functions = functions
undesired_sequence_functions = []


############################################################
# The actual planner
def seek_plan_robot(agents: Dict[str, Agent], agent_name, sols, uncontrollable_agent_name = "human", fails=None, previous_action=None):
    result = _seek_plan_robot(agents, agent_name, sols, uncontrollable_agent_name, fails, previous_action)

    _merge_sols(sols)

    # Add begin action for each solution
    begin_action = Operator("BEGIN", [], uncontrollable_agent_name, None, None, None)
    for s in sols:
        first_action = get_first_action(s)
        if first_action.name != "BEGIN":
            first_action.predecessor = begin_action
            first_action.previous = begin_action
            if first_action not in begin_action.next:
                begin_action.next.append(first_action)

    return result

def _seek_plan_robot(agents: Dict[str, Agent], agent_name, sols, uncontrollable_agent_name = "human", fails=None, previous_action=None):
    if fails is None:
        fails = []

    # If robot agenda is empty
    if agents[agent_name].tasks == []:
        _backtrack_plan(agents[uncontrollable_agent_name].plan[-1])
        sols.append(agents[uncontrollable_agent_name].plan[-1])
        # print("=> BRANCH OVER <=")
        return True

    # Else, handle first task to do in the robot agenda
    task = agents[agent_name].tasks[0]

    # print("HATPEHDA> task = {} {} {}".format(task.agent, task.name, task.parameters))

    # print("\nagenda = ", end='')
    # for taski in agents[agent_name].tasks:
    #     print(" {}{},".format(taski.name, taski.parameters), end='')
    # print("")
    # print_state(agents[agent_name].state)
    # print("\ntreating task name={}".format(task.name))

    # If the first task is an operator known by the robot
    if task.name in agents[agent_name].operators:
        # print("is an operator")

        # CHECK IF FEASIBLE, AND IF SO THEN ADD IT TO THE ROBOT PLAN
        # Get the operator and tries to apply it on a copy of agents
        operator = agents[agent_name].operators[task.name]
        newagents = copy.deepcopy(agents)
        result = operator(newagents, newagents[agent_name].state, agent_name, *task.parameters)

        # if not feasible
        if result == False:
            #print(task.name + " not feasible...")
            return False

        # else, if it's feasible
        # set the cost of the operator
        # remove the task from the robot agenda and put it in the robot plan
        newagents[agent_name].tasks = newagents[agent_name].tasks[1:]
        action = Operator.copy_new_id(task)
        action.cost = result[1]
        action.previous = previous_action
        newagents[agent_name].plan.append(action)

        # CHECK TRIGGERS OF OTHER AGENTS
        # check the triggers of every other agent than the robot
        for a in agents:
            if a == agent_name:
                continue
            for t in newagents[a].triggers:
                triggered = t(newagents, newagents[a].state, a)
                if triggered != False:
                    triggered_subtasks = []
                    for sub in triggered:
                        if sub[0] in agents[a].methods:
                            triggered_subtasks.append(AbstractTask(sub[0], sub[1:], a, None, None, [], len(newagents[a].methods[sub[0]])))
                        elif sub[0] in agents[a].operators:
                            triggered_subtasks.append(Operator(sub[0], sub[1:], a, None, None, newagents[a].operators[sub[0]]))
                        else:
                            raise TypeError(
                                "Error: the trigger function '{}'"
                                "returned a subtask '{}' which is neither in the methods nor in the operators "
                                "of agent '{}'".format(t.__name__, sub[0], a)
                            )
                    newagents[a].tasks = triggered_subtasks + newagents[a].tasks
                    break

        # MANAGE NEXT POSSIBLE HUMAN ACTION, PLAN WITH THEM
        # Get the next possible actions of the human
        new_possible_agents = get_human_next_actions(newagents, uncontrollable_agent_name, previous_action=action)
        if new_possible_agents == False:
            # No action is feasible for the human
            #print("No action feasible for the human")
            return False

        # For each possible action of the human, plan for the robot
        for ag in new_possible_agents:
            # print(" H : {} {}".format(ag["human"].plan[-1].name, ag["human"].plan[-1].parameters))
            _seek_plan_robot(ag, agent_name, sols, uncontrollable_agent_name, fails, previous_action=ag[uncontrollable_agent_name].plan[-1])
        # print("robot plan:", newagents[agent_name].plan, "human plan:", newagents[uncontrollable_agent_name].plan)
        return True

    # Else if it's in the known methods of the robot
    if task.name in agents[agent_name].methods:
        # print("is a method")
        # get the decompositions of the method
        decompos = agents[agent_name].methods[task.name]
        reachable_agents = []
        # print("decompos= {}".format(decompos))
        for i, decompo in enumerate(decompos):
            newagentsdecompo = copy.deepcopy(agents)
            result = decompo(newagentsdecompo, newagentsdecompo[agent_name].state, agent_name, *task.parameters)
            if result is None:
                raise TypeError(
                    "Error: the decomposition function: {} of task {} has returned None. It should return a list or False.".format(decompo.__name__,  task.name))
            if result != False:
                multi_decompos = None
                # print("result={}".format(result))
                if result != [] and isinstance(result[0], str) and result[0] == "MULTI":
                    multi_decompos = result[1]
                else:
                    multi_decompos = [result]
                # print("multi_decompos={}".format(multi_decompos))
                for multi_decompo in multi_decompos:
                    # print("multi_decompo={}".format(multi_decompo))
                    newagents = copy.deepcopy(newagentsdecompo)
                    subtasks_obj = []
                    for sub in multi_decompo:
                        # print("sub={}".format(sub))
                        if sub[0] in agents[agent_name].methods:
                            subtasks_obj.append(AbstractTask(sub[0], sub[1:], agent_name, task, i, [], len(agents[agent_name].methods[sub[0]])))
                        elif sub[0] in agents[agent_name].operators:
                            subtasks_obj.append(Operator(sub[0], sub[1:], agent_name, task, i, agents[agent_name].operators[sub[0]]))
                        else:
                            raise TypeError(
                                "Error: the decomposition function '{}' of task '{}' "
                                "returned a subtask '{}' which is neither in the methods nor in the operators "
                                "of agent '{}'".format(decompo.__name__, task.name, sub[0], agent_name)
                            )
                    # print("subtasks_obj={}".format(subtasks_obj))
                    newagents[agent_name].tasks = subtasks_obj + newagents[agent_name].tasks[1:]
                    reachable_agents.append(newagents)
        if reachable_agents == []:
            # No decomposition is achievable for this task
            #print("No decompo found for the robot for task:", task.name)
            #print("robot plan:", agents[agent_name].plan, "human plan:", agents[uncontrollable_agent_name].plan)
            return False
        else:
            for ag in reachable_agents:
                _seek_plan_robot(ag, agent_name, sols, uncontrollable_agent_name, fails, previous_action)
            return True

    return False

def get_human_next_actions(agents, agent_name, previous_action):
    global human_prediction_type
    if human_prediction_type == HumanPredictionType.FIRST_APPLICABLE_ACTION:
        sols = []
        next_actions = get_first_applicable_action(agents, agent_name, sols)
        if next_actions is False:
            newagents = copy.deepcopy(agents)
            wait_action = Operator("WAIT", [], agent_name, None, 0, None)
            wait_action.previous = previous_action
            newagents[agent_name].plan.append(wait_action)  # Default action
            return [newagents]
        else:
            return sols
    elif human_prediction_type == HumanPredictionType.ALL_APPLICABLE_ACTIONS:
        sols = []
        result = get_all_applicable_actions(agents, agent_name, sols, previous_action=previous_action)
        if result is False:
            raise Exception("Error during human HTN exploration")
        if sols == []:
            newagents = copy.deepcopy(agents)
            wait_action = Operator("WAIT", [], agent_name, None, 0, None)
            wait_action.previous = previous_action
            newagents[agent_name].plan.append(wait_action)  # Default action
            return [newagents]
        else:
            return sols

def get_all_applicable_actions(agents, agent_name, solutions, previous_action):
    if agents[agent_name].tasks == []:
        newagents = copy.deepcopy(agents)
        idle = Operator("IDLE", [], agent_name, None, 0, None)
        idle.previous = previous_action
        newagents[agent_name].plan.append(idle)
        solutions.append(newagents)
        return
    task = agents[agent_name].tasks[0]
    if task.name in agents[agent_name].operators:
        operator = agents[agent_name].operators[task.name]
        newagents = copy.deepcopy(agents)
        result = operator(newagents, newagents[agent_name].state, agent_name, *task.parameters)
        if result == False:
            return
        newagents[agent_name].tasks = newagents[agent_name].tasks[1:]
        action = Operator.copy_new_id(task)
        action.cost = result[1]
        action.previous = previous_action
        newagents[agent_name].plan.append(action)
        for a in agents:
            if a == agent_name:
                continue
            for t in newagents[a].triggers:
                triggered = t(newagents, newagents[a].state, a)
                if triggered != False:
                    triggered_subtasks = []
                    for sub in triggered:
                        if sub[0] in newagents[a].methods:
                            triggered_subtasks.append(AbstractTask(sub[0], sub[1:], a, None, None, [], len(newagents[a].methods[sub[0]])))
                        elif sub[0] in newagents[a].operators:
                            triggered_subtasks.append(Operator(sub[0], sub[1:], a, None, None, newagents[a].operators[sub[0]]))
                        else:
                            raise TypeError(
                                "Error: the trigger function '{}'"
                                "returned a subtask '{}' which is neither in the methods nor in the operators "
                                "of agent '{}'".format(t.__name__, sub[0], a)
                            )
                    newagents[a].tasks = triggered_subtasks + newagents[a].tasks
                    break
        solutions.append(newagents)
        return
    if task.name in agents[agent_name].methods:
        decompos = agents[agent_name].methods[task.name]
        for i, decompo in enumerate(decompos):
            newagentsdecompo = copy.deepcopy(agents)
            result = decompo(newagentsdecompo, newagentsdecompo[agent_name].state, agent_name, *task.parameters)
            if result != False:
                subtaskss = None
                if result != [] and isinstance(result[0], str) and result[0] == "MULTI":
                    subtaskss = result[1]
                else:
                    subtaskss = [result]
                for subtasks in subtaskss:
                    newagents = copy.deepcopy(newagentsdecompo)
                    subtasks_obj = []
                    for sub in subtasks:
                        if sub[0] in agents[agent_name].methods:
                            subtasks_obj.append(AbstractTask(sub[0], sub[1:], agent_name, task, i, [], len(agents[agent_name].methods[sub[0]])))
                        elif sub[0] in agents[agent_name].operators:
                            subtasks_obj.append(Operator(sub[0], sub[1:], agent_name, task, i, agents[agent_name].operators[sub[0]]))
                        else:
                            raise TypeError(
                                "Error: the decomposition function '{}' of task '{}' "
                                "returned a subtask '{}' which is neither in the methods nor in the operators "
                                "of agent '{}'".format(decompo.__name__, task.name, sub[0], agent_name)
                            )
                    newagents[agent_name].tasks = subtasks_obj + newagents[agent_name].tasks[1:]
                    get_all_applicable_actions(newagents, agent_name, solutions, previous_action)
        return
    #print("looking for:", task.name, "not a task nor an action of agent", agent_name)
    return False

def get_first_applicable_action(agents, agent_name, solutions):
    raise NotImplementedError("Not implemented yet.")

def _backtrack_plan(last_action):
    action = last_action
    while action is not None:
        if action.previous is not None and action not in action.previous.next:
            action.previous.next.append(action)
        action = action.previous

def _merge_sols(sols):
    tasks = {}
    for sol in sols:
        primitive = sol
        while primitive.previous is not None:
            if primitive.previous.id not in tasks:
                tasks[primitive.previous.id] = primitive.previous
                prev = primitive.previous
            else:
                prev = primitive.previous
                primitive.previous = tasks[primitive.previous.id]
                if primitive.id not in [t.id for t in tasks[primitive.previous.id].next]:
                    tasks[primitive.previous.id].next.append(primitive)
            primitive = prev
    return sols

def select_conditional_plan(sols, controllable_agent_name, uncontrollable_agent_name, cost_dict={}):
    all_branches = []
    all_costs = []
    def explore_policy(agents, action, cost):
        new_agents = copy.deepcopy(agents) # check if needed

        # Get the cost of the operator
        cost_op = 0.0
        if action.name != "BEGIN":
            if action.name == "IDLE":
                cost_op = idle_cost_function()
            elif action.name == "WAIT":
                cost_op = wait_cost_function()
            else:
                cost_op = action.cost
        cost += cost_op

        # Check undesired states
        undesired_state_penalty = 0.0
        for undesired_state_check in undesired_state_functions:
            undesired_state_penalty += undesired_state_check(new_agents)
        cost += undesired_state_penalty

        # Explore
        # print("{}{}".format(action.name, action.parameters))
        # print(" -> id={} cost={} state_penalty={} total={}".format(action.id, cost_op, undesired_state_penalty, cost))

        if action.next is None or action.next == []:

            # Check undesired sequence
            undesired_sequence_penalty = 0.0

            last_action = copy.deepcopy(action)
            first_action = _backtrack_plan_one_branch(last_action, None) # set the action.next to only the specific action of this branch

            for undesired_sequence_check in undesired_sequence_functions:
                undesired_sequence_penalty += undesired_sequence_check(first_action)
                cost += undesired_sequence_penalty

            # print("============ branch ({}) seq_penalty={} total_cost={}\n".format(len(all_branches)+1, undesired_sequence_penalty, cost))
            all_branches.append(first_action)
            all_costs.append(cost)

            return cost

        if action.agent == controllable_agent_name:
            total_cost = 0
            # FUTURE WORK:
            # Rather than just a mean, do a small optimization scheme
            # that takes into account the average cost but also
            # the worst and best cost possible
            # For example if we have 3 possible human choices leading to
            # 2 very good scenario (small costs) but 1 really really bad (huge cost)
            # we can maybe bet on the rationnality of the human to not choose the worst action
            # and bet on the 2 very good scenarios
            for successor in action.next:
                total_cost += explore_policy(new_agents, successor, cost)
            return total_cost / len(action.next)

        elif action.agent == uncontrollable_agent_name:
            min_cost = explore_policy(new_agents, action.next[0], cost)
            min_i_cost = 0
            for i, successor in enumerate(action.next[1:]):
                new_cost = explore_policy(new_agents, successor, cost)
                if new_cost < min_cost:
                    min_i_cost = i + 1
                    min_cost = new_cost
            action.next = [action.next[min_i_cost]]
            action.next[0].predecessor = action
            return min_cost

    # Explore policies
    begin_action = get_first_action(sols[0])
    act = copy.deepcopy(begin_action)
    cost = explore_policy(agents, act, 0)

    return act, cost, all_branches, all_costs

def _backtrack_plan_one_branch(action, next):
    if action is not None:
        action.next = next
        if action.previous is not None:
            return _backtrack_plan_one_branch(action.previous, action)
        else:
            return _backtrack_plan_one_branch(None, action)
    else:
        return next

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
