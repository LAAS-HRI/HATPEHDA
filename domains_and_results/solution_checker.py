import dill
import sys

import matplotlib.pyplot as plt


import CommonModule as CM
import ConcurrentModule as ConM
import time

def inactivity_deadlock(state):
    pairs = state.children
    if len(pairs)==1:
        p = pairs[0]
        if not p.is_final() and p.is_passive():
            return True
    return False

def new_check_solution(goal_condition_in):
    sys.setrecursionlimit(100000)

    states_with_issue = []

    print("Checking solution... ", end="", flush=True)
    s_t = time.time()

    if len(CM.g_FINAL_IPSTATES)==0:
        print("Done! - %.5fs" %(time.time()-s_t))
        print(f"ERROR: No leaf!")
        return False

    for ips in CM.g_FINAL_IPSTATES:
        s = CM.g_PSTATES[ips]
        if (not goal_condition_in(s.state)) or inactivity_deadlock(s):
            states_with_issue.append(s)
    print("Done! - %.5fs" %(time.time()-s_t))

    if len(states_with_issue)>0:
        print(f"\tErroneous Steps detected ! [{len(states_with_issue)}]\n")
        print('\t', end="")
        for s in states_with_issue:
            print(f"({s.id}) ", end="")
        print("\n")
        return False
    else:
        print("\tAll clear !")
        return True
    
if __name__ == "__main__":
    from new_cart import goal_condition
    new_check_solution(goal_condition_in=goal_condition)


