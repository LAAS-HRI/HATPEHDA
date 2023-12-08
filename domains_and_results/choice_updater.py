from typing import Any, Dict, List, Tuple
import dill
import graphviz
import sys
import concurrent.futures
import time
from copy import deepcopy 
import numpy as np

import matplotlib.pyplot as plt


import CommonModule as CM
import ConcurrentModule as ConM


def load(filename):

    print(f"Loading solution '{filename}' ... ", end="", flush=True)
    s_t = time.time()

    domain_name, pstates, final_pstates = dill.load(open(CM.path + filename, "rb"))

    print("Loaded! - %.2fs" %(time.time()-s_t))

    return domain_name, pstates, final_pstates

def load_solution():
    """
    Loads the previously produced solution.
    The domain name is retreived and returned and as well as the solution tree and the initial step.
    """

    filename = "search_space.p"
    if len(sys.argv)>1:
        filename = sys.argv[1]

    return load(filename)

def dump(filename):
    print(f"Dumping policy '{filename}' ...  ", end="", flush=True)
    s_t = time.time()

    dill.dump((g_domain_name, CM.g_PSTATES, CM.g_FINAL_IPSTATES), open(CM.path + filename, "wb"))

    print("Dumped! - %.2fs" %(time.time()-s_t))

def dump_solution():
    filename = "policy.p"
    if len(sys.argv)>1:
        filename = sys.argv[1][:-2] + "_policy.p"

    dump(filename)


##################################################################################


nb_traces = 0
def compute_nb_traces(ips=0):
    global nb_traces
    ps = CM.g_PSTATES[ips]
    for i, action_pair in enumerate(ps.children):
        if action_pair.child!=None:
            child_ips = action_pair.child
            if child_ips in CM.g_FINAL_IPSTATES:
                nb_traces += 1
            else:
                compute_nb_traces(ips=child_ips)

    return nb_traces

##################################

from new_render_graph import render_generation_step
RENDER_GENERATION_STEP = False

def update_robot_policy():

    to_merge = set()
    to_propagate = set()
    for leaf_ips in CM.g_FINAL_IPSTATES:
        to_propagate = to_propagate.union({leaf_ips})
        leaf_ps = CM.g_PSTATES[leaf_ips]
        leaf_ps.best_metrics = {
            "TimeTaskCompletion" : 0,
            "TimeEndHumanDuty" : 0,
            "HumanEffort" : 0,
            "GlobalEffort" : 0,
            "PassiveWhileHolding" : 0,
            "NbDrop" : 0,
            "Annoying": 0,
            "PlaceFirstBar": 0,

            "NbLastPassiveH": 0,
        }

    if RENDER_GENERATION_STEP:
        i=0;render_generation_step(filename=f"generation_{i}");i+=1
    while not check_over(to_merge, to_propagate):
        to_merge, to_propagate = propagate(to_merge, to_propagate)
        if RENDER_GENERATION_STEP:
            render_generation_step(filename=f"generation_{i}");i+=1
        to_merge, to_propagate = merge(to_merge, to_propagate)
        if RENDER_GENERATION_STEP:
            render_generation_step(filename=f"generation_{i}");i+=1

def propagate(to_merge, to_propagate):
    """
    for each pstate in the given to_propagate set, computes and propagates best metrics in every 
    parent action pairs until reaching a parent pstate has more than one children (excluding 
    double_pass).
    The best metrics are stored in the action pairs just below the pstates with more than one 
    children. 
    The to_propagate set is cleared and the to_merge set is updated with every parent pstate that
    stopped the propagation.
    """
    while len(to_propagate):
        ips_to_propagate = to_propagate.pop()
        ps_to_propagate = CM.g_PSTATES[ips_to_propagate]

        for parent_ap in ps_to_propagate.parents:
            # TODO: ignore IDLE|IDLE pair ?
            # compute new metrics
            new_metrics = deepcopy(ps_to_propagate.best_metrics)
            # standard
            new_metrics["TimeTaskCompletion"] += 1
            if parent_ap.human_action.is_passive() and new_metrics["HumanEffort"]==0:
                new_metrics["NbLastPassiveH"] += 1
            new_metrics["TimeEndHumanDuty"] = new_metrics["TimeTaskCompletion"] - new_metrics["NbLastPassiveH"]
            if not parent_ap.human_action.is_passive():
                new_metrics["HumanEffort"] += 1
                new_metrics["GlobalEffort"] += 1
            if not parent_ap.robot_action.is_passive():
                new_metrics["GlobalEffort"] += 1
            # domain specific
            if parent_ap.human_action.is_passive() and ps_to_propagate.state.holding.get('H')!=None:
                new_metrics["PassiveWhileHolding"] += 1
            if parent_ap.robot_action.is_passive() and ps_to_propagate.state.holding.get('R')!=None:
                new_metrics["PassiveWhileHolding"] += 1
            if parent_ap.robot_action.name=="drop":
                new_metrics["NbDrop"] += 1
            if parent_ap.human_action.name=="drop":
                new_metrics["NbDrop"] += 1

            # if both loc clear and robot pick one in center
            if ps_to_propagate.state.stack.get('l1')==None\
            and ps_to_propagate.state.stack.get('l2')==None\
            and parent_ap.robot_action.name=='pick' and parent_ap.robot_action.parameters[0]=='y1':
                new_metrics['Annoying'] += 1
            if ps_to_propagate.state.stack.get('l4')==None\
            and ps_to_propagate.state.stack.get('l5')==None\
            and parent_ap.robot_action.name=='pick' and parent_ap.robot_action.parameters[0]=='o1':
                new_metrics['Annoying'] += 1

            # if robot places first ping bar
            if parent_ap.robot_action.name=='place' and parent_ap.robot_action.parameters[0]=='l3' and parent_ap.robot_action.parameters[1]=='p2':
                new_metrics['PlaceFirstBar'] += 1

            # store in action_pair
            parent_ap.best_metrics = new_metrics

            # check if should keep propagating
            parent_ps = CM.g_PSTATES[parent_ap.parent] #type: CM.PState
            if len(parent_ps.children) > 2:
                to_merge = to_merge.union({parent_ps.id})
            else:
                parent_ps.best_metrics = new_metrics
                parent_ap.best = True
                parent_ap.best_compliant = True
                to_propagate = to_propagate.union({parent_ps.id})

    return to_merge, to_propagate

def merge(to_merge, to_propagate):
    """
    For each pstate in the given to_merge set, check if each child (action_pair) has a stored best
    metrics. If not the pstate isn't ready to be merged and remains in the to_merge set. If so, 
    compare the best metrics and identify+mark the best action pair from this step. Store in the 
    pstate the best metrics. Additionaly, for each human option identify the best metrics
    and thus the best compliant pair and mark it. The pstate is removed from the to_merge set and 
    added to the to_propagate set.
    """
    new_to_merge = set()
    for ips_to_merge in to_merge:
        ps_to_merge = CM.g_PSTATES[ips_to_merge]

        ok_to_merge = True
        for c in ps_to_merge.children:
            if not c.is_passive() and c.best_metrics == None:
                ok_to_merge = False
                break
        
        if not ok_to_merge:
            new_to_merge = new_to_merge.union({ips_to_merge})
        else:
            # merge + identify best choices
            # identify best pair/metrics, mark and best pair, and store in pstate
            sorted_pairs = list(np.sort( np.array( ps_to_merge.children ) ))
            best_pair = sorted_pairs[0]
            best_pair.best = True
            best_pair.best_compliant = True
            ps_to_merge.best_metrics = best_pair.best_metrics

            # extract human option and find best compliant pair for each human option
            # extract human actions
            human_actions = set()
            for p in ps_to_merge.children:
                # if p.human_action.is_passive():
                #     human_actions = human_actions.union( { "PASSIVE" } )
                # else:
                human_actions = human_actions.union( { f"{p.human_action.name}{p.human_action.parameters}" } )
            # for each human action
            for ha in human_actions:
                if ha == f"{best_pair.human_action.name}{best_pair.human_action.parameters}":
                    continue
                # filter non relevant pairs in a copy of sorted pairs
                cp_sorted_pairs = sorted_pairs[:]
                for p in ps_to_merge.children:
                    # if p.human_action.is_passive() and ha!="PASSIVE":
                    #     cp_sorted_pairs.remove(p)
                    if f"{p.human_action.name}{p.human_action.parameters}" != ha:
                        cp_sorted_pairs.remove(p)

                # first is best compliant pair
                best_compliant_pair = cp_sorted_pairs[0]
                best_compliant_pair.best_compliant = True

            # add to to_propagate
            to_propagate = to_propagate.union({ips_to_merge})

    return new_to_merge, to_propagate

def check_over(to_merge, to_propagate):
    """
    The process is over when both sets (to_propagate and to_merge) are empty.
    """
    return len(to_merge)==0 and len(to_propagate)==0

##################################

def exec_chrono(func, msg):
    s_t = time.time()
    print(''.join([msg, ' ... ']), end='', flush=True)
    r = func()
    print("Done! - %.2fs" %(time.time()-s_t))
    return r

def str_print_metrics_priority(metrics):
    s = '{'

    criteria = ConM.get_exec_prefs()[ConM.G_POLICY_NAME]

    for c in criteria:
        c = c[0]
        s += f"'{c}': {metrics[c]}, "

    s = s[:-2] + '}'

    return s


def main():
    global g_domain_name
    sys.setrecursionlimit(100000)


    ##############################################

    ConM.setPolicyName('task_end_early')
    g_domain_name, pstates, final_pstates = load_solution()
    CM.g_PSTATES = pstates
    CM.g_FINAL_IPSTATES = final_pstates
    print(f"Number of leaves: {len(CM.g_FINAL_IPSTATES)}")
    print(f"Nb states = {len(CM.g_PSTATES)}")
    exec_chrono(update_robot_policy, f"Computing robot policy {ConM.G_POLICY_NAME}")
    print("\tbest_metrics: ", str_print_metrics_priority(CM.g_PSTATES[0].best_metrics))
    dump(f'policy_{ConM.G_POLICY_NAME}.p')

    ConM.setPolicyName('human_min_work')
    g_domain_name, pstates, final_pstates = load_solution()
    CM.g_PSTATES = pstates
    CM.g_FINAL_IPSTATES = final_pstates
    print(f"Number of leaves: {len(CM.g_FINAL_IPSTATES)}")
    print(f"Nb states = {len(CM.g_PSTATES)}")
    exec_chrono(update_robot_policy, f"Computing robot policy {ConM.G_POLICY_NAME}")
    print("\tbest_metrics: ", str_print_metrics_priority(CM.g_PSTATES[0].best_metrics))
    dump(f'policy_{ConM.G_POLICY_NAME}.p')

    ConM.setPolicyName('human_free_early')
    g_domain_name, pstates, final_pstates = load_solution()
    CM.g_PSTATES = pstates
    CM.g_FINAL_IPSTATES = final_pstates
    print(f"Number of leaves: {len(CM.g_FINAL_IPSTATES)}")
    print(f"Nb states = {len(CM.g_PSTATES)}")
    exec_chrono(update_robot_policy, f"Computing robot policy {ConM.G_POLICY_NAME}")
    print("\tbest_metrics: ", str_print_metrics_priority(CM.g_PSTATES[0].best_metrics))
    dump(f'policy_{ConM.G_POLICY_NAME}.p')

    ##############################################
    
    # g_domain_name, pstates, final_pstates = load_solution()
    # CM.g_PSTATES = pstates
    # CM.g_FINAL_IPSTATES = final_pstates
    # print(f"Number of leaves: {len(CM.g_FINAL_IPSTATES)}")
    # print(f"Nb states = {len(CM.g_PSTATES)}")
    # nb_traces = exec_chrono(compute_nb_traces, "Computing nb traces")
    # print("\tnb_traces= ", nb_traces)

    ##############################################


    # TODO: like in new render, remove pairs where best_compliant=False, save only the policy
    #  implies that has to load original sol file to update policy
    
if __name__ == "__main__":
    main()