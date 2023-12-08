#!/usr/bin/env python3

from copy import deepcopy
import hatpehda
from hatpehda.hatpehda import Operator
from hatpehda.hatpehda import get_last_actions
from hatpehda.hatpehda import _backtrack_plan_one_branch


#########################################
# Class and global variable declaration #
#########################################
steps = []
class Step:
    def __init__(self, action):
        self.action = action
        self.agents = None
        self.effects = [] # effets = [Modif(attribute, key, val)]
class Modif:
    def __init__(self, attribute, key, val):
        self.attribute = attribute
        self.key = key
        self.val = val

class Link:
    def __init__(self, step=None, target=None):
        self.step = step
        self.target = target


#########
# Debug #
#########
def print_states(agents):
    for ag in agents:
        agent = agents[ag]
        print("state {} agent :".format(agent.name))
        for attribute in get_state_attributes(agents["robot"].state):
            print("  {} = {}".format(attribute, getattr(agent.state, attribute)))
        return None # Only first agent, the robot


#################
# Sub functions #
#################
def get_state_attributes(state):
    all_attributes = dir(state)
    attributes = deepcopy(all_attributes)
    for att in all_attributes:
        if att[0] == '_' and att[1] == '_' and att[-2] == '_' and att[-1] == '_': # test separatly to handle attribute name with only one caracter
            attributes.remove(att)
    return attributes

def set_link(links, step, target, type):
    """
    Creates a new link from step to target and adds it
    only to the given link list if not already in
    """

    # Prevents a step to link with itself
    if step.action == target.action:
        return None

    # Checks if the link doesn't already exist
    for l in links:
        if step.action == l.step.action and target.action == l.target.action:
            return None

    # Creates the link and adds it
    new_link = Link(step, target)
    links.append(new_link)

    # Debug #
    # if type == "s":
    #     print("support ", end='')
    # if type == "t":
    #     print("threat ", end='')
    # print("set_link : {} => {}".format(new_link.step.action, new_link.target.action))

    return None

def get_app_steps(agents, other_steps):
    """
    Returns all applicable steps contained in the list "other_steps"
    from the states given in the "agents" param
    """
    applicable_steps = []

    # For each step in other_steps, try to apply the operator of the step
    for other_step in other_steps:
        newagents = deepcopy(agents)
        if other_step.action.name == "BEGIN":
            continue
        elif other_step.action.name == "IDLE":
            applicable_steps.append(other_step)
        else:
            operator = newagents[other_step.action.agent].operators[other_step.action.name]
            result = operator(newagents, newagents[other_step.action.agent].state, other_step.action.agent, *other_step.action.parameters)
            if result != False:
                applicable_steps.append(other_step)

    return applicable_steps

def compute_applicable_changes(previous_applicable_steps, applicable_steps):
    """
    Computes and returns the new applicable steps and the no longer
    applicable steps from previous and current list of applicable steps
    """
    new_applicable_steps = []
    no_longer_applicable_steps = []

    # new applicable steps
    for step in applicable_steps:
        if step not in previous_applicable_steps:
            new_applicable_steps.append(step)
    # no longer applicable steps
    for step in previous_applicable_steps:
        if step not in applicable_steps:
            no_longer_applicable_steps.append(step)

    # Debug #
    # print("\nCompute new applicable")
    # print("applicable_steps:")
    # for step in applicable_steps:
    #     print("  {}".format(step.action))
    # print("previous_applicable_steps:")
    # for step in previous_applicable_steps:
    #     print("  {}".format(step.action))
    # print("new applicable steps :")
    # for new_app_step in new_applicable_steps:
    #     print("  {}".format(new_app_step.action))
    # print("no longer applicable steps :")
    # for no_long_app_steps in no_longer_applicable_steps:
    #     print("  {}".format(no_long_app_steps.action))

    return new_applicable_steps, no_longer_applicable_steps

def apply_step(agents, step):
    """
    Applies the operator of the given step in the state
    given in agents and returns the new state in newagents
    """
    newagents = deepcopy(agents)
    if step.action.name != "IDLE":
        agent_name = step.action.agent
        operator = agents[agent_name].operators[step.action.name]
        result = operator(newagents, newagents[agent_name].state, agent_name, *step.action.parameters)
    return newagents

def apply_effect(agents, step):
    """
    Only applies the effects of the given step in the state
    given in agents, returns the new state in newagents
    #TODO : apply effects according to each agent
    """
    newagents = deepcopy(agents)

    for ag in newagents.values():
        # append
        for add in step.effects["append"]:
            if not isinstance(getattr(ag.state, add.attribute)[add.key], list):
                getattr(ag.state, add.attribute)[add.key] = add.val
            else:
                getattr(ag.state, add.attribute)[add.key].append(add.val)
        # remove
        for rm in step.effects["remove"]:
            if isinstance(getattr(ag.state, rm.attribute)[rm.key], list):
                try:
                    getattr(ag.state, rm.attribute)[rm.key].remove(rm.val)
                except:
                    # print("no value to remove : step={} rm.attribute={} rm.key={} rm.val={}".format(step.action, rm.attribute, rm.key, rm.val))
                    continue

    return newagents

def compute_effects(previous_agents, current_agents):
    """
    Computes and returns the effects of a step by checking the differences
    between the given previous state (previous_agents) and the given current state
    (current_agents). The attributes parameter helps to check each attribute of the states
    #TODO : differenciate effects for each agents
    """
    previous_state = previous_agents["robot"].state
    current_state = current_agents["robot"].state
    modifs = {"remove": [], "append": []}
    attributes = get_state_attributes(current_state)
    for attribute in attributes:
        if attribute == "attributes":
            continue
        if getattr(current_state, attribute) != getattr(previous_state, attribute):
            # creation of new key in operators is forbidden
            for key in getattr(current_state, attribute):

                # if the key has been modified
                if getattr(previous_state, attribute)[key] != getattr(current_state, attribute)[key]:

                    # put the elements in a list if it is not one already
                    previous_elem = getattr(previous_state, attribute)[key]
                    if not isinstance(getattr(previous_state, attribute)[key], list):
                        previous_elem = [previous_elem]
                    curr_elem = getattr(current_state, attribute)[key]
                    if not isinstance(getattr(current_state, attribute)[key], list):
                        curr_elem = [curr_elem]

                    # for each element in previous state key
                    # if not present in next state key then add remove
                    for x in previous_elem:
                        if x not in curr_elem:
                            # print("{} element {} not in next state key {}".format(attribute, x, key))
                            modif = Modif(attribute, key, x)
                            modifs["remove"].append(modif)

                    # for each element in next state key
                    # if not present in previous state key then add apprend
                    for x in curr_elem:
                        if x not in previous_elem:
                            # print("{} element {} not in previous state key {}".format(attribute, x, key))
                            modif = Modif(attribute, key, x)
                            modifs["append"].append(modif)
    return modifs

def treat_plans(all_branches):
    # Treats plans #
    if not isinstance(all_branches, list):
        last_actions = get_last_actions(all_branches)
        for action in last_actions:
            while action is not None:
                action = action.previous
        branches = []
        for last_action in last_actions:
            last_bis = deepcopy(last_action)
            first_action = _backtrack_plan_one_branch(last_bis, None)
            branches.append(first_action)
    else:
        branches = all_branches

    plans = []

    for branch in branches:
        plan = []
        action = branch
        while action is not None:
            plan.append(action)
            action = action.next
        plans.append(plan)

    return plans

def initialize(initial_agents, plan):
    """
    Initialize the data structure by first recovering all actions of the plan
    and then creating a step for each action. A step has an associated action of the plan,
    a world state after being applied, and effects.
    """

    # Initializes steps #
    steps = []

    # First action in plan must be BEGIN, without any effects
    first_step = Step(plan[0])
    first_step.agents = initial_agents
    first_step.effects = {"remove":[], "append":[]}
    steps.append(first_step)

    # Creates the steps
    step_agents = deepcopy(initial_agents)
    for action in plan[1:]:

        # Removes IDLE action from the steps
        if action.name == "IDLE":
            continue

        # Creates step from the action in the plan
        step = Step(action)

        # Adds the world state (step_agents) after being applied
        previous_agents = deepcopy(step_agents)
        step_agents = apply_step(step_agents, step)
        step.agents = step_agents

        # Computes and adds the effects of the action
        effects = compute_effects(previous_agents, step_agents)
        step.effects = effects

        steps.append(step)

    # Debug
    # for i, step in enumerate(steps):
    #     print("\nstep {} : {}".format(i, step.action))
    #     print_states(step.agents)
    #     print("effects=")
    #     print("  rm  =", end="")
    #     for rm in step.effects["remove"]:
    #         print(" ({}, {}, {})".format(rm.attribute, rm.key, rm.val), end="")
    #     print("\n  add =", end='')
    #     for add in step.effects["append"]:
    #         print(" ({}, {}, {})".format(add.attribute, add.key, add.val), end="")
    #     print("")

    return steps

def look_for_supports(steps, initial_agents):
    supports = []

    # Explore the plan from the last action
    for i in range(len(steps)-1, 0, -1): # sauf BEGIN
        step = steps[i]
        newagents = deepcopy(initial_agents)
        # print("\n==> step {} : {} <==".format(i, step.action))

        # Apply effects of all the supports of step from the initial state
        has_supports = False
        for sup in supports:
            if sup.target.action == step.action:
                # print("support {}".format(sup.step.action))
                has_supports = True
                newagents = apply_effect(newagents, sup.step)
        # print_states(newagents)

        # Check if step is applicable
        applicable_steps =  get_app_steps(newagents, steps)

        # print("applicable_steps :")
        # for app_step in applicable_steps:
            # print("  {}".format(app_step.action))

        if step in applicable_steps:
            if not has_supports:
                set_link(supports, steps[0], step, "s")
            # print("A tous ses supports !")
        else:
            # print("hum il en manque")
            has_all_its_supports = False
            j = i - 1
            while not has_all_its_supports and j>=0:
                # print("\nj={} {}".format(j, steps[j].action))

                # Apply effect of all supports in state of step j-1
                newagents = deepcopy(steps[j-1].agents)
                for sup in supports:
                    if sup.target.action == step.action:
                        # print("known support {}".format(sup.step.action))
                        newagents = apply_effect(newagents, sup.step)

                # Apply effects of step j in state j-1, once effects of supports have been applied
                before_applicable_steps = get_app_steps(newagents, steps)
                newagents = apply_effect(newagents, steps[j])
                after_applicable_steps = get_app_steps(newagents, steps)
                new_applicable_steps, no_longer_app_steps = compute_applicable_changes(before_applicable_steps, after_applicable_steps)

                # If step i is appicable, step j is a support of step i (step)
                if step in new_applicable_steps:
                    set_link(supports, steps[j], step, "s")

                # Check if step has all its supports
                # Apply effects of all the supports of step from the initial state
                # print("check if has all its supports, apply known supports :")
                check_all_agents = deepcopy(initial_agents)
                for sup in supports:
                    if sup.target.action == step.action:
                        # print("  support {}".format(sup.step.action))
                        check_all_agents = apply_effect(check_all_agents, sup.step)
                # print_states(check_all_agents)
                # Check if step is applicable
                applicable_steps =  get_app_steps(check_all_agents, steps)
                # print("applicable_steps far :")
                # for app_step in applicable_steps:
                    # print("  {}".format(app_step.action))
                if step in applicable_steps:
                    # print("Has all its supports !")
                    has_all_its_supports = True
                else:
                    # print("Still missing some supports ..")
                    j -= 1

    return supports

def look_for_threats(steps):
    threats = []

    # Core algorithm
    previous_app_steps = []
    for step in steps:
        # print("\n===> THREATS step={}".format(step.action))
        curr_agents = step.agents
        # print_states(curr_agents)

        # print("get applicable steps which are after the current step:")
        app_steps = get_app_steps(curr_agents, steps[steps.index(step)+1:])
        # print("app steps:")
        # for app_step in app_steps:
        #     print("  {}".format(app_step.action))

        # new_app_steps, no_long_app_steps = compute_applicable_changes(previous_app_steps, app_steps)
        # print("new applicable steps :")
        # for new_app_step in new_app_steps:
            # print("  {}".format(new_app_step.action))

        for app_step in app_steps:
            # print("=>test {}".format(app_step.action))
            # print_states(curr_agents)

            # Add step as support of new_app_step
            # set_link(supports, step, new_app_step)

            # virtually_apply(new_app_step)
            indep_agents = apply_step(curr_agents, app_step)
            # print_states(indep_agents)


            # get list indep_applicable_actions
            indep_app_steps = get_app_steps(indep_agents, steps)
            # print("indep app steps")
            # for indep_app_step in indep_app_steps:
            #     print(indep_app_step.action)

            # from indep_applicable_actions and currently_applicable_actions compute indep_new_applicable_actions and indep_no_longer_applicable_actions
            indep_new_app_steps, indep_no_longer_app_steps = compute_applicable_changes(app_steps, indep_app_steps)

            # for indep_new_app_step in indep_new_app_steps:
                # set new_app_step as support of indep_new_app_step
                # set_link(supports, new_app_step, indep_new_app_step)
            for indep_no_longer_app_step in indep_no_longer_app_steps:
                # set new_app_step as threat for indep_no_longer_app_step
                set_link(threats, app_step, indep_no_longer_app_step, "t")

        previous_app_steps = app_steps

    return threats

def remove_double_links(links):
    newlinks=[]

    for link in links:
        already_in = False
        for l in newlinks:
            if link.step.action.id == l.step.action.id and link.target.action.id == l.target.action.id:
                already_in = True
                break
        if not already_in:
            newlinks.append(link)

    return newlinks

def remove_bidirectional_threats(threats):
    removed = False
    for threat1 in threats:
        for threat2 in threats:
            if threat1 == threat2:
                continue
            if threat2.step == threat1.target and threat2.target == threat1.step:
                threats.remove(threat1)
                threats.remove(threat2)
                print("removed link {} <=> {}".format(threat1.step.action, threat1.target.action))
                removed = True
                break
        if removed:
            break

    if removed :
        remove_bidirectional_threats(threats)
    else:
        return None

#############
# Main algo #
#############
def compute_causal_links(agents, all_branches):
    """
    Computes and returns the causal links of all the possible plans
    """

    initial_agents = deepcopy(agents)

    # Converts the plans to lists of actions
    plans = treat_plans(all_branches)

    # For each plan in the given possible plans
    supports = []
    threats = []
    for plan in plans:
        # Initialization
        steps = initialize(initial_agents, plan)

        # Find supports
        supports += look_for_supports(steps, initial_agents)

        # Find  threats in the plan
        threats += look_for_threats(steps)

    # Double links are created with common action at the beginning of every plan
    supports = remove_double_links(supports)
    threats = remove_double_links(threats)
    remove_bidirectional_threats(threats)

    return supports, threats
