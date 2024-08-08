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

    domain_name, pstates, final_pstates, back_edges = dill.load(open(CM.path + filename, "rb"))

    print("Loaded! - %.2fs" %(time.time()-s_t))

    return domain_name, pstates, final_pstates, back_edges

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

    dill.dump((g_domain_name, CM.g_PSTATES, CM.g_FINAL_IPSTATES, CM.g_BACK_EDGES), open(CM.path + filename, "wb"))

    print("Dumped! - %.2fs" %(time.time()-s_t))

##################################################################################


g_lengths = []
def compute_traces(ips=0, current_length=0):
    global g_lengths
    ps = CM.g_PSTATES[ips]
    for i, action_pair in enumerate(ps.children):
        if action_pair.child!=None:
            child_ips = action_pair.child
            if child_ips in CM.g_FINAL_IPSTATES:
                g_lengths.append(current_length+1)
            else:
                compute_traces(ips=child_ips, current_length=current_length+1)

##################################

from render import render_generation_step
RENDER_GENERATION_STEP = False



def generate_policy(policy_name):
    global g_domain_name
    g_domain_name, CM.g_PSTATES, CM.g_FINAL_IPSTATES, CM.g_BACK_EDGES = load_solution()

    CM.g_use_robot_metrics = True

    ConM.setPolicyName(policy_name)
    print(f"Number of leaves: {len(CM.g_FINAL_IPSTATES)}")
    print(f"Nb states = {len(CM.g_PSTATES)}")
    exec_chrono(update_policy, f"Computing robot policy {ConM.G_POLICY_NAME}")
    print("\tbest_metrics: ", str_print_metrics_priority(CM.g_PSTATES[0].get_best_metrics()))
    dump(f'policy_{ConM.G_POLICY_NAME}.p')

def add_human_policy(policy_name_to_load, policy_name_to_add):
    global g_domain_name
    g_domain_name, CM.g_PSTATES, CM.g_FINAL_IPSTATES, CM.g_BACK_EDGES = load("policy_"+policy_name_to_load+".p")

    CM.g_use_robot_metrics = False

    ConM.setPolicyName(policy_name_to_add)
    exec_chrono(update_policy, f"Computing human policy {policy_name_to_add}")
    print("\tbest_metrics: ", str_print_metrics_priority(CM.g_PSTATES[0].get_best_metrics()))
    
    dump(f'policy_{policy_name_to_load}_{policy_name_to_add}.p')


default_metrics={
    "TimeTaskCompletion" : 0,
    "TimeEndHumanDuty" : 0,
    "HumanEffort" : 0,
    "GlobalEffort" : 0,
    "NbLastPassiveH": 0, # temp var

    # Cart
    "AxelsFirst": 0,
    "BodyFirst": 0,
    "PassiveWhileHolding" : 0,

    # Stack
    "PassiveWhileHolding" : 0,
    "NbDrop" : 0,
    "Annoying": 0,
    "PlaceFirstBar": 0,
}

def update_policy():
    to_merge = set()
    to_propagate = set()
    for leaf_ips in CM.g_FINAL_IPSTATES:
        to_propagate = to_propagate.union({leaf_ips})
        leaf_ps = CM.g_PSTATES[leaf_ips]
        leaf_ps.set_best_metrics(deepcopy(default_metrics))

    ###############################
    if RENDER_GENERATION_STEP:
        i=0;render_generation_step(to_merge,to_propagate,filename=f"generation_{i}");i+=1
    ###############################

    while not check_over(to_merge, to_propagate):
        to_merge, to_propagate = propagate(to_merge, to_propagate)

        ###############################
        if RENDER_GENERATION_STEP:
            render_generation_step(to_merge,to_propagate,filename=f"generation_{i}");i+=1
        ###############################

        to_merge, to_propagate = merge(to_merge, to_propagate)

        ###############################
        if RENDER_GENERATION_STEP:
            render_generation_step(to_merge,to_propagate,filename=f"generation_{i}");i+=1
        ###############################

def compute_new_metrics_generic(new_metrics, parent_ap):
    new_metrics["TimeTaskCompletion"] += 1
    if parent_ap.human_action.is_passive() and new_metrics["HumanEffort"]==0:
        new_metrics["NbLastPassiveH"] += 1
    new_metrics["TimeEndHumanDuty"] = new_metrics["TimeTaskCompletion"] - new_metrics["NbLastPassiveH"]
    if not parent_ap.human_action.is_passive():
        new_metrics["HumanEffort"] += 1
        new_metrics["GlobalEffort"] += 1
    if not parent_ap.robot_action.is_passive():
        new_metrics["GlobalEffort"] += 1

    return new_metrics

def compute_new_metrics_domain_specific_cart(new_metrics, parent_ap, ps_to_propagate):
    # AxelsFirst
    if parent_ap.robot_action.name=="useTool" and ps_to_propagate.state.holding['R']=='rivet':
        if ps_to_propagate.state.link_axel1_floor and ps_to_propagate.state.link_axel2_floor:
            if  not ps_to_propagate.state.link_body_floor\
            and not ps_to_propagate.state.link_wheel1_axel1\
            and not ps_to_propagate.state.link_wheel2_axel1\
            and not ps_to_propagate.state.link_wheel3_axel2\
            and not ps_to_propagate.state.link_wheel4_axel2:
                new_metrics['AxelsFirst'] += 1

    # BodyFirst
    if parent_ap.robot_action.name=="useTool" and ps_to_propagate.state.holding['R']=='welder':
        if  ps_to_propagate.state.link_body_floor:
            if  not ps_to_propagate.state.link_axel1_floor\
            and not ps_to_propagate.state.link_axel2_floor\
            and not ps_to_propagate.state.link_wheel1_axel1\
            and not ps_to_propagate.state.link_wheel2_axel1\
            and not ps_to_propagate.state.link_wheel3_axel2\
            and not ps_to_propagate.state.link_wheel4_axel2:
                new_metrics['BodyFirst'] += 1

    # PassiveWhileHolding
    if parent_ap.human_action.is_passive() and ps_to_propagate.state.holding.get('H')!=None:
        new_metrics["PassiveWhileHolding"] += 1
    if parent_ap.robot_action.is_passive() and ps_to_propagate.state.holding.get('R')!=None:
        new_metrics["PassiveWhileHolding"] += 1

    return new_metrics

def compute_new_metrics_domain_specific_stack(new_metrics, parent_ap, ps_to_propagate):
    if parent_ap.human_action.is_passive() and ps_to_propagate.state.holding.get('H')!=None:
        new_metrics["PassiveWhileHolding"] += 1
    if parent_ap.robot_action.is_passive() and ps_to_propagate.state.holding.get('R')!=None:
        new_metrics["PassiveWhileHolding"] += 1
    if parent_ap.robot_action.name=="drop":
        new_metrics["NbDrop"] += 1
    if parent_ap.human_action.name=="drop":
        new_metrics["NbDrop"] += 1

    # Annoying
    if parent_ap.robot_action.name=='pick' and parent_ap.robot_action.parameters[0]=='y1':
        parent_ps = CM.g_PSTATES[parent_ap.parent]
        for ap in parent_ps.children:
            if ap.human_action.name=='pick' and ap.human_action.parameters[0]=='y1':
                new_metrics['Annoying'] += 5
                break
        for ap in parent_ps.children:
            if ap.robot_action.name=='pick' and ap.robot_action.parameters[0]=='r1':
                new_metrics['Annoying'] += 3
                break
    if parent_ap.human_action.name=='pick' and parent_ap.human_action.parameters[0]=='y1':
        parent_ps = CM.g_PSTATES[parent_ap.parent]
        found = False
        for ap in parent_ps.children:
            if ap.robot_action.name=='pick' and ap.robot_action.parameters[0]=='y1':
                found = True
                break
        if found:
            if parent_ap.robot_action.is_passive():
                new_metrics['Annoying'] -= 3

    if parent_ap.robot_action.name=='pick' and parent_ap.robot_action.parameters[0]=='o1':
        parent_ps = CM.g_PSTATES[parent_ap.parent]
        for ap in parent_ps.children:
            if ap.human_action.name=='pick' and ap.human_action.parameters[0]=='o1':
                new_metrics['Annoying'] += 5
                break
        for ap in parent_ps.children:
            if ap.robot_action.name=='pick' and ap.robot_action.parameters[0]=='s1':
                new_metrics['Annoying'] += 3
                break
    if parent_ap.human_action.name=='pick' and parent_ap.human_action.parameters[0]=='o1':
        parent_ps = CM.g_PSTATES[parent_ap.parent]
        found = False
        for ap in parent_ps.children:
            if ap.robot_action.name=='pick' and ap.robot_action.parameters[0]=='o1':
                found = True
                break
        if found:
            if parent_ap.robot_action.is_passive():
                new_metrics['Annoying'] -= 3

    if parent_ap.robot_action.name=='pick' and parent_ap.robot_action.parameters[0]=='w1':
        parent_ps = CM.g_PSTATES[parent_ap.parent]
        for ap in parent_ps.children:
            if ap.human_action.name=='pick' and ap.human_action.parameters[0]=='w1':
                new_metrics['Annoying'] += 5
                break
        for ap in parent_ps.children:
            if ap.robot_action.name=='pick' and ap.robot_action.parameters[0]=='s1':
                new_metrics['Annoying'] += 3
                break
    if parent_ap.human_action.name=='pick' and parent_ap.human_action.parameters[0]=='w1':
        parent_ps = CM.g_PSTATES[parent_ap.parent]
        found = False
        for ap in parent_ps.children:
            if ap.robot_action.name=='pick' and ap.robot_action.parameters[0]=='w1':
                found = True
                break
        if found:
            if parent_ap.robot_action.is_passive():
                new_metrics['Annoying'] -= 3

    # if robot places first ping bar
    if parent_ap.robot_action.name=='place' and parent_ap.robot_action.parameters[0]=='l3' and parent_ap.robot_action.parameters[1]=='p2':
        new_metrics['PlaceFirstBar'] += 1

    return new_metrics

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

            new_metrics = deepcopy(ps_to_propagate.get_best_metrics())
            
            new_metrics = compute_new_metrics_generic(new_metrics, parent_ap)
            # new_metrics = compute_new_metrics_domain_specific_cart(new_metrics, parent_ap, ps_to_propagate)
            new_metrics = compute_new_metrics_domain_specific_stack(new_metrics, parent_ap, ps_to_propagate)
            
            # store in action_pair
            parent_ap.set_best_metrics(new_metrics)

            # check if should keep propagating
            parent_ps = CM.g_PSTATES[parent_ap.parent] #type: CM.PState
            if len(parent_ps.children) > 2:
                to_merge = to_merge.union({parent_ps.id})
            else:
                parent_ps.set_best_metrics(new_metrics)
                parent_ap.set_best(True)
                parent_ap.set_best_compliant(True)
                parent_ap.set_best_compliant_h(True)
                to_propagate = to_propagate.union({parent_ps.id})
                for c in parent_ps.children:
                    c.rank = 0

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
            if not c.is_passive() and c.get_best_metrics() == None:
                ok_to_merge = False
                break
        
        if not ok_to_merge:
            new_to_merge = new_to_merge.union({ips_to_merge})
        else:
            # merge + identify best choices
            # identify best pair/metrics, mark and best pair, and store in pstate
            sorted_pairs = list(np.sort( np.array( ps_to_merge.children ) ))
            for i,p in enumerate(sorted_pairs):
                p.rank = i
            best_pair = sorted_pairs[0]
            best_pair.set_best(True)
            best_pair.set_best_compliant(True)
            best_pair.set_best_compliant_h(True)
            ps_to_merge.set_best_metrics(best_pair.get_best_metrics())

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
                best_compliant_pair.set_best_compliant(True)

            # extract robot option and find best compliant_h pair for each robot option
            # extract robot actions
            robot_actions = set()
            for p in ps_to_merge.children:
                robot_actions = robot_actions.union( { f"{p.robot_action.name}{p.robot_action.parameters}" } )
            # for each robot action
            for ra in robot_actions:
                if ra == f"{best_pair.robot_action.name}{best_pair.robot_action.parameters}":
                    continue
                # filter non relevant pairs in a copy of sorted pairs
                cp_sorted_pairs = sorted_pairs[:]
                for p in ps_to_merge.children:
                    if f"{p.robot_action.name}{p.robot_action.parameters}" != ra:
                        cp_sorted_pairs.remove(p)

                # first is best compliant pair
                best_compliant_pair = cp_sorted_pairs[0]
                best_compliant_pair.set_best_compliant_h(True)
            
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
    print("Done! - %.5fs" %(time.time()-s_t))
    return r

def str_print_metrics_priority(metrics):
    s = '{'

    criteria = ConM.get_exec_prefs()[ConM.G_POLICY_NAME]

    for c in criteria:
        c = c[0]
        s += f"'{c}': {metrics[c]}, "

    s = s[:-2] + '}'

    return s

def compute_number_of_traces():
    print(f"Number of leaves: {len(CM.g_FINAL_IPSTATES)}")
    print(f"Nb states = {len(CM.g_PSTATES)}")
    exec_chrono(compute_traces, "Computing nb traces")

    lengths = np.array(g_lengths)
    print("\t nb=", len(lengths))
    print("\t mean= %.2f" %np.mean(lengths))
    print("\t std= %.2f" %np.std(lengths))
    print("\t min=", np.min(lengths))
    print("\t max=", np.max(lengths))

def main():
    sys.setrecursionlimit(100000)

    ##############################################

    # Cart
    # generate_policy('cart_esti11')
    # generate_policy('cart_esti12')

    # Stack
    generate_policy('task_end_early')
    # generate_policy('human_min_work')
    # generate_policy('fake_human_free_early')
    # generate_policy('real_human_free_early')


    ##############################################

    # Cart 
    # add_human_policy('cart_esti11', 'cart_pref1')
    # add_human_policy('cart_esti12', 'cart_pref1')

    # Stack 
    # add_human_policy('task_end_early', 'human_min_work')
    # add_human_policy('fake_human_free_early', 'real_human_free_early')


    ##############################################

    # compute_number_of_traces()

    ##############################################
    
    
if __name__ == "__main__":
    main()