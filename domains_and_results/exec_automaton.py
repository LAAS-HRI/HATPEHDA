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

def simulate_exec(regime):

    trace = [] # list of ConM.ActionPair 
    state = CM.g_PSTATES[0]

    HUMAN_FIRST = regime=="HF"
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

    return metrics

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

from choice_updater import compute_new_metrics_generic
from choice_updater import compute_new_metrics_domain_specific_cart
from choice_updater import compute_new_metrics_domain_specific_stack
from choice_updater import default_metrics

from choice_updater import generate_policy, add_human_policy

if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    g_domain_name, CM.g_PSTATES, CM.g_FINAL_IPSTATES, CM.g_BACK_EDGES = load(f"search_space.p")

    r_pref_dyn = [
        ("TimeTaskCompletion",      False),
        ("TimeEndHumanDuty",        False),
    ]
    r_pref_static = [
        ("HumanEffort",             False),
        ("GlobalEffort",            False),
        ("PassiveWhileHolding",     False),
        ("NbDrop",                  False),
    ]
    h_pref_dyn = [
        ("TimeTaskCompletion",      False),
        ("TimeEndHumanDuty",        False),
        ("HumanEffort",             False),
        ("GlobalEffort",            False),
    ]
    h_pref_static = [
        ("PassiveWhileHolding",     False),
        ("NbDrop",                  False),
    ]


    permu_h = list( permutations(h_pref_dyn) )
    permu_r = list( permutations(r_pref_dyn) )

    all_metrics = []

    for r_p in permu_r:
        for h_p in permu_h:
            ConM.g_prefs["r_pref"] = list(r_p) + r_pref_static
            ConM.g_prefs["h_pref"] = list(h_p) + h_pref_static
            generate_policy("r_pref", load_dump=False)
            add_human_policy("r_pref", "h_pref", load_dump=False)

            all_metrics.append( simulate_exec("HF") )

            

    # Get min and max of metrics
    min_robot_metric = {}
    max_robot_metric = {}
    for m in ConM.g_prefs["r_pref"]:
        for metric in all_metrics:
            try:
                min_robot_metric[m[0]] = min(min_robot_metric[m[0]], metric[m[0]])
                max_robot_metric[m[0]] = max(max_robot_metric[m[0]], metric[m[0]])
            except:
                min_robot_metric[m[0]] = metric[m[0]]
                max_robot_metric[m[0]] = metric[m[0]]
    min_human_metric = {}
    max_human_metric = {}
    for m in ConM.g_prefs["h_pref"]:
        for metric in all_metrics:
            try:
                min_human_metric[m[0]] = min(min_human_metric[m[0]], metric[m[0]])
                max_human_metric[m[0]] = max(max_human_metric[m[0]], metric[m[0]])
            except:
                min_human_metric[m[0]] = metric[m[0]]
                max_human_metric[m[0]] = metric[m[0]]

    # Compute score
    scores = [] # (r_score, h_score)
    i = 0
    for r_p in permu_r:
        for h_p in permu_h:

            metrics = all_metrics[i]
            i+=1

            r_min_list = []
            r_max_list = []
            r_list = []
            for m in permu_r:
                r_min_list.append( metrics[m[0]])
                r_max_list.append( metrics[m[0]])
                r_list.append( metrics[m[0]] )
            h_min_list = []
            h_max_list = []
            h_list = []
            for m in permu_h:
                h_min_list.append( metrics[m[0]])
                h_max_list.append( metrics[m[0]])
                h_list.append( metrics[m[0]] )

            # Get score
            R_score = compute_score(r_list, r_min_list, r_max_list)
            H_score = compute_score(h_list, h_min_list, r_max_list)
            print(f"R_score= {R_score}\nH_score= {H_score}")
