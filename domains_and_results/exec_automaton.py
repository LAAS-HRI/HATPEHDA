from __future__ import annotations
from typing import Any, Dict, List, Tuple
from copy import deepcopy
import random
import dill
import sys
from enum import Enum
import logging as lg
import logging.config
import matplotlib.pyplot as plt
from itertools import permutations
from progress.bar import IncrementalBar
import time


class IdResult(Enum):
    NOT_NEEDED=0
    FAILED=1

DEBUG = False
INPUT = False
########
# DEBUG = True
# INPUT = True

import ConcurrentModule as ConM
import CommonModule as CM

## LOGGER ##
logging.config.fileConfig(CM.path + 'log.conf')

#############
## LOADING ##
#############
def load(filename):

    print(f"Loading solution '{filename}' ... ", end="", flush=True)
    s_t = time.time()

    domain_name, pstates, final_pstates, back_edges = dill.load(open(CM.path + filename, "rb"))

    print("Loaded! - %.2fs" %(time.time()-s_t))

    return domain_name, pstates, final_pstates, back_edges

def sum_n_first_int(n):
    s = 0
    for i in range(1,n+1):
        s += i
    return s

def compute_score(current, mini, maxi):
    '''
    Receives an ordered list of values.
    The order corresponds to the priority order of metrics in pref
    Each value corresponds to the associated metric
    current is the metrics to obtain a score from
    mini the minimal value of each metric
    maxi the maximal value of each metric
    '''
    N = len(current)
    D = (0.05 * N - 1.0) / (sum_n_first_int(N-1) - (N-1) * N)

    # Compute weights according to N
    weights = [ (1.0 + sum_n_first_int(N-1) * D) / N ]
    for i in range(N-1):
        weights.append( weights[-1] - D )
    print(f"weights = {weights}")

    s = 0
    for w in weights:
        s += w
    print(f"sum weights = {s}")

    # Weighted score
    score = 0.0
    for i in range(N):
        normalized_m = (current[i] - mini[i])/(maxi[i] - mini[i])
        score += weights[i] * normalized_m

    return score

def get_pair_str(pair):
    h_str = ""
    if pair.human_action.is_idle():
        h_str = "IDLE"
    elif pair.human_action.is_wait():
        h_str = "WAIT"
    elif pair.human_action.is_pass():
        h_str = "PASS"
    else:
        h_str = f"{pair.human_action.name}{pair.human_action.parameters}"

    r_str = ""
    if pair.robot_action.is_idle():
        r_str = "IDLE"
    elif pair.robot_action.is_wait():
        r_str = "WAIT"
    elif pair.robot_action.is_pass():
        r_str = "PASS"
    else:
        r_str = f"{pair.robot_action.name}{pair.robot_action.parameters}"

    return f"{h_str} | {r_str}"


from choice_updater import compute_new_metrics_generic
from choice_updater import compute_new_metrics_domain_specific_cart
from choice_updater import compute_new_metrics_domain_specific_stack
from choice_updater import default_metrics

if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    robot_esti = "task_end_early"
    human_pref = "human_min_work"
    g_domain_name, CM.g_PSTATES, CM.g_FINAL_IPSTATES, CM.g_BACK_EDGES = load(f"policy_{robot_esti}_{human_pref}.p")

	# best_metrics:  {'TimeTaskCompletion': 11, 'TimeEndHumanDuty': 8, 'HumanEffort': 8, 'GlobalEffort': 16, 'PassiveWhileHolding': 0, 'NbDrop': 0}
	# best_metrics:  {'TimeTaskCompletion': 23, 'TimeEndHumanDuty': 22, 'HumanEffort': 12, 'GlobalEffort': 22, 'PassiveWhileHolding': 18, 'NbDrop': 3}

    min_robot_esti = [11, 8, 8, 16, 0, 0]
    max_robot_esti = [23, 22, 12, 22, 18, 3]

    min_human_pref = [24, 2, 18, 0, 19, 6, 1]
    max_human_pref = [-9, 12, 22, 14, 23, 22, 3]


    """
    Load policy including both robot and human choices
    Simulate execution, each agent following its policy
    Save the list of simulated ActionPair (Trace)
    Find a way to compute the metrics of such trace
    Make sure to obtain the minimal and maximal values of both policy
    Send the obtained metrics, and associated boundary values to the score computation
    """

    trace = [] # list of ConM.ActionPair 
    state = CM.g_PSTATES[0]

    HUMAN_FIRST = True
    ROBOT_FIRST = not HUMAN_FIRST

    while state.id not in CM.g_FINAL_IPSTATES:

        if HUMAN_FIRST:
            # Get best human action (according to human_pref)
            first_pair = None
            for pair in state.children:
                if pair._h_best:
                    first_pair = pair
                    break

            # Get best compliant robot action (according to robot_esti)
            compliant_pair = None
            for pair in state.children:
                if CM.Action.are_similar(first_pair.human_action, pair.human_action):
                    if pair._best_compliant:
                        compliant_pair = pair
                        break
        
        if ROBOT_FIRST:
            # Get best robot action (according to robot_esti)
            first_pair = None
            for pair in state.children:
                if pair._best:
                    first_pair = pair
                    break

            # Get best compliant human action (according to human_pref)
            compliant_pair = None
            for pair in state.children:
                if CM.Action.are_similar(first_pair.robot_action, pair.robot_action):
                    if pair._h_best_compliant_h:
                        compliant_pair = pair

        # Save action pair in trace
        trace.append(compliant_pair)

        # Get next state
        state = CM.g_PSTATES[compliant_pair.child]

    # Show trace and end state
    print("Trace (H | R):")
    for p in trace:
        print(get_pair_str(p))
    print(f"End state = {trace[-1].child}")
        
    # Compute metrics of trace
    metrics = deepcopy(default_metrics)
    i = -1
    p = trace[i]
    while p.parent != 0:
        metrics = compute_new_metrics_generic(metrics, p)
        metrics = compute_new_metrics_domain_specific_stack(metrics, p, CM.g_PSTATES[p.child])
        # metrics = compute_new_metrics_domain_specific_cart(metrics, p, CM.g_PSTATES[p.child])

        i -= 1
        p = trace[i]

    print(metrics)

    # Convert metrics to ordered list
    print("\nRobot metrics:")
    r_list = []
    for i, m in enumerate(ConM.g_prefs[robot_esti]):
        print(f"\t{m[0]}: {metrics[m[0]]} ({min_robot_esti[i]} > {max_robot_esti[i]})")
        r_list.append( metrics[m[0]] )

    print("\nHuman metrics:")
    h_list = []
    for i, m in enumerate(ConM.g_prefs[human_pref]):
        print(f"\t{m[0]}: {metrics[m[0]]} ({min_human_pref[i]} > {max_human_pref[i]})")
        h_list.append( metrics[m[0]] )

    # Get score
    R_score = compute_score(r_list, min_robot_esti, max_robot_esti)
    H_score = compute_score(h_list, min_human_pref, max_human_pref)
    print(f"R_score= {R_score}\nH_score= {H_score}")

    print("voila")

    exit()

    ##############################################


    r_criteria = [
        ("TimeEndHumanDuty",    False),
        ("HumanEffort",         False),
        ("TimeTaskCompletion",  False),
        ("GlobalEffort",        False),
        # ("RiskConflict",      False),
    ]
    h_criteria = [
        ("TimeEndHumanDuty",    True),
        ("HumanEffort",         True),
        ("TimeTaskCompletion",  True),
        ("GlobalEffort",        True),
        # ("RiskConflict",      False),
    ]
    do_plot=False
    solutions = []


    permu_r = list( permutations(r_criteria) )
    permu_h = list( permutations(h_criteria) )

    # permu_r = [ r_criteria ]
    # permu_h = [ h_criteria ]
    # do_plot=True

    bar = IncrementalBar("Computing", max=len(permu_r)*len(permu_h), width=40, suffix='%(index)d/%(max)d - %(elapsed_td)s - ETA=%(eta_td)s')

    for r_p in permu_r:
        for h_p in permu_h:
            r_ranked_leaves, h_ranked_leaves = set_choices(begin_step,r_p,h_p)
            result = main_exec(domain_name, solution_tree, begin_step,r_p,h_p, r_ranked_leaves, h_ranked_leaves)

            if result[0]==-1:
                print("Failed... -1")
            else:
                (id, r_score, h_score, seed, r_ranked_leaves, h_ranked_leaves) = result

                # find step with with id
                nb_sols = len(h_ranked_leaves)
                solution_step = None
                for l in begin_step.get_final_leaves():
                    if l.id == id:
                        solution_step = l
                        break
                score_r = convert_rank_to_score(solution_step.get_f_leaf().branch_rank_r, nb_sols)
                score_h = convert_rank_to_score(solution_step.get_f_leaf().branch_rank_h, nb_sols)
                solutions.append( (score_h,score_r) )
                # print(f"solution: r#{score_r:.2f}-h#{score_h:.2f}-{nb_sols}")
                bar.next()

                
                if do_plot:
                    xdata = []
                    ydata = []
                    nb_sols = len(h_ranked_leaves)
                    for l in h_ranked_leaves:
                        xdata.append( convert_rank_to_score(l.get_f_leaf().branch_rank_h, nb_sols) )
                        ydata.append( convert_rank_to_score(find_r_rank_of_id(h_ranked_leaves, l.id),nb_sols) )

                    # plt.figure(figsize=(3, 3))
                    plt.plot(xdata, ydata, 'b+')
                    plt.plot([score_h], [score_r], 'ro')
                    plt.xlabel("score human solution")
                    plt.ylabel("score robot solution")
                    plt.show()
    print("\nfinish")

    dill.dump(solutions, open(CM.path + "solution_exec.p", "wb"))
    # print(solutions)


