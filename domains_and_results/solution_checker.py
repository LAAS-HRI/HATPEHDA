import dill
import sys

import matplotlib.pyplot as plt


import CommonModule as CM
import ConcurrentModule as ConM
import time

def goal_condition_step(step):
    if step.is_leaf:
        for p in step.get_pairs():
            state = p.end_agents.state
            if goal_condition(state):
                return True
    return False

def inactivity_deadlock(step):
    pairs = step.get_pairs()
    if step.is_leaf and len(pairs)==1:
        p = pairs[0]
        if p.robot_action.is_wait() and p.human_action.is_wait_turn()\
        and p.previous.robot_action.is_wait_turn() and p.previous.human_action.is_wait():
            return True
        if p.human_action.is_wait() and p.human_action.is_wait_turn()\
        and p.previous.human_action.is_wait_turn() and p.previous.robot_action.is_wait():
            return True
        if p.robot_action.is_wait() and p.human_action.is_wait():
            return True
    return False

def check_solution(begin_step ,goal_condition_in):
    global goal_condition
    sys.setrecursionlimit(100000)

    goal_condition = goal_condition_in

    steps_to_explore = [begin_step]
    steps_with_issue = []

    print("Checking solution... ", end="", flush=True)
    s_t = time.time()
    while len(steps_to_explore):

        s = steps_to_explore.pop()
        if s.is_leaf:
            if (s.is_final() and not goal_condition_step(s)) or inactivity_deadlock(s):
                steps_with_issue.append(s)
        else:
            steps_to_explore += s.children
    print("Done! - %.2fs" %(time.time()-s_t))

    if len(steps_with_issue)>0:
        print(f"\tErroneous Steps detected ! [{len(steps_with_issue)}]\n")
        print('\t', end="")
        for s in steps_with_issue:
            print(f"({s.id}) ", end="")
        print("\n")
    else:
        print("\tAll clear !")


