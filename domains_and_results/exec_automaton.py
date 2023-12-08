from __future__ import annotations
from typing import Any, Dict, List, Tuple
from copy import deepcopy
import random
import pickle
import dill
import sys
from enum import Enum
import logging as lg
import logging.config
import matplotlib.pyplot as plt
from itertools import permutations
from progress.bar import IncrementalBar

import cProfile
import pstats


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
from stack_equi import *
# from arrangement import *
# from conflict_pick import *
# from simple import *

class WrongException(Exception):
    pass

## LOGGER ##
logging.config.fileConfig(CM.path + 'log.conf')

#############
## LOADING ##
#############
begin_step = None
def load_solution():
    """
    Loads the previously produced solution.
    The domain name is retreived and returned and as well as the solution tree and the initial step.
    """
    dom_n_sol = dill.load(open(CM.path + "dom_n_sol.p", "rb"))

    domain_name = dom_n_sol[0]
    solution_tree = dom_n_sol[1]
    init_step = solution_tree[0]

    return domain_name, solution_tree, init_step

def set_choices(init_step,r_criteria,h_criteria):

    final_leaves = init_step.get_final_leaves()

    # ConM.compute_metrics(final_leaves)

    r_ranked_leaves = ConM.sorting_branches(final_leaves, r_criteria, is_robot=True) #type: List[ConM.Step]
    h_ranked_leaves = ConM.sorting_branches(final_leaves, h_criteria, is_robot=False) #type: List[ConM.Step]

    ConM.update_robot_choices(init_step)
    ConM.update_human_choices(init_step)

    # f = open("test.txt", "w")
    # for rl in r_ranked_leaves:
    #     metrics=""
    #     for m in rl.get_f_leaf().branch_metrics.values():
    #         metrics+=f"{m} "
    #     metrics=metrics[:-1]
    #     f.write(f"#{rl.get_f_leaf().branch_rank_r}\t\t({rl.id})\t\t[{metrics}]\n")
    # f.close()

    # f = open("ranks.txt", "w")
    # f.write("R sorting\n")
    # f.write(ConM.get_str_ranked_branches(r_ranked_leaves, robot=True))
    # f.write("H sorting\n")
    # f.write(ConM.get_str_ranked_branches(h_ranked_leaves, robot=False))
    # f.close()

    return r_ranked_leaves, h_ranked_leaves

###############
## EXECUTION ##
###############
def execution_simulation(begin_step: ConM.Step, r_pref, h_pref, r_ranked_leaves, h_ranked_leaves):
    """
    Main algorithm 
    """
    curr_step = get_first_step(begin_step)
    nb_of_degradation = 0
    while not exec_over(curr_step):
        wait_step_start(curr_step)
        MOCK_save_best_reachable_solution_for_human(curr_step)
        MOCK_H_action_choice(curr_step)

        if is_ID_needed(curr_step):
            result_id = MOCK_run_id_phase(curr_step)
            if ID_successful(result_id):
                RA = pick_best_valid_RA(curr_step, result_id)
            else:
                RA = pick_valid_passive(curr_step)
        else:
            lg.debug("ID not needed.")
            result_id = IdResult.NOT_NEEDED
            RA = curr_step.SRA

        MOCK_execute_RA(RA)
                  

        # MOCK_H_LRDe(curr_step, RA)
        HA = MOCK_assess_human_action(result_id)
        curr_step = get_next_step(curr_step, HA, RA)
        MOCK_save_best_reachable_solution_for_human_after_robot_choice(curr_step)
        if MOCK_robot_has_degraded_human_best_solution():
            nb_of_degradation +=1
            if nb_of_degradation >= 1:
                r_ranked_leaves, h_ranked_leaves = adjust_robot_preferences(begin_step,h_pref,h_pref)

        wait_step_end()
    lg.debug(f"END => {curr_step}")
    # return int(curr_step.id)
    return int(curr_step.id), curr_step.get_f_leaf().branch_rank_r, curr_step.get_f_leaf().branch_rank_h, r_ranked_leaves, h_ranked_leaves


#########################
## MOCK Human behavior ##
#########################
HC = None
g_p_lrde = None
g_p_lrdo = None
def MOCK_H_action_choice(step: ConM.Step):
    """
    Simulate the human choice of action.
    Common actions are equiprobable, and LRD has a defined probability P_PICK_LRD.
    LRD can be made equiprobable with common actions if P_PICK_LRD is set to -1.
    """
    global HC

    if len(step.human_options)==1:
        HC=step.human_options[0].human_action
    else:
        if HUMAN_TYPE=="POLICY":
            HC = step.best_human_pair.human_action
        if HUMAN_TYPE=="RANDOM":
            global g_p_lrde, g_p_lrdo
            g_p_lrde = None
            possible_human_actions = [ho.human_action for ho in step.human_options]

            # Compute weights - probas
            p_lrde, p_lrdo, p_equi = get_lrd_probas(len(possible_human_actions))
            weights = [p_equi for i in range(len(possible_human_actions)-1)] + [p_lrde+p_lrdo]
            g_p_lrde = p_lrde
            g_p_lrdo = p_lrdo

            # Make random choice
            HC = random.choices(possible_human_actions, weights=weights)[0]

def MOCK_H_LRDe(step: ConM.Step, RA: CM.Action):
    """
    If the human performed a LRD action it can be a Let_Robot_Decide.
    In such case, the human actually performs another action during the step (HC must be updated)
    """
    if HUMAN_TYPE!="RANDOM":
        return None
    global HC
    if HC.name=="LRD":
        p_Le_L = g_p_lrde/(g_p_lrde + g_p_lrdo)
        if random.random()<p_Le_L:
            lg.debug("Human only let robot decide")
            valid_pairs = []
            for p in step.get_pairs():
                if p.human_action.name!="LRD" and CM.Action.are_similar(p.robot_action, RA):
                    valid_pairs.append(p)
            if len(valid_pairs)>0:
                HC = random.choice(valid_pairs).human_action

g_best_reachable_human_solution = None
def MOCK_save_best_reachable_solution_for_human(step: ConM.Step):
    if not HUMAN_UPDATING:
        return
    global g_best_reachable_human_solution
    s = step

    while not s.is_final:
        s = s.best_human_pair.next[0].get_in_step()
    
    g_best_reachable_human_solution = s


g_best_reachable_human_solution_after_robot_choice = None
def MOCK_save_best_reachable_solution_for_human_after_robot_choice(step: ConM.Step):
    if not HUMAN_UPDATING:
        return
    global g_best_reachable_human_solution_after_robot_choice
    s = step

    while not s.is_final:
        s = s.best_human_pair.next[0].get_in_step()
    
    g_best_reachable_human_solution_after_robot_choice = s

def MOCK_robot_has_degraded_human_best_solution():
    if not HUMAN_UPDATING:
        return False
    rank_before = g_best_reachable_human_solution.get_f_leaf().branch_rank_h
    rank_after = g_best_reachable_human_solution_after_robot_choice.get_f_leaf().branch_rank_h

    lg.debug(f"#{rank_before} -> #{rank_after}")

    return rank_after>rank_before

def adjust_robot_preferences(begin_step,r_pref,h_pref):
    r_ranked_leaves, h_ranked_leaves = set_choices(begin_step,r_pref,h_pref)
    lg.debug("ROBOT PREFERENCES ALIGNED !!!!")
    return (r_ranked_leaves, h_ranked_leaves)
    

##########################
## MOCK Robot execution ##
##########################
def MOCK_execute_RA(RA: CM.Action):
    lg.debug(f"Execute Robot Action {RA}")

def MOCK_run_id_phase(step: ConM.Step):
    """
    Simulate the identification phase.
    LRD are always identified.
    For other human actions, the ID phase has a P_SUCCESS_ID_PHASE chance to succeed.
    If successful, there is a P_WRONG_ID chance that the ID the actually wrong.
    """
    lg.debug("Start ID phase...")
    if random.random()<P_SUCCESS_ID_PHASE:
        possible_other_human_actions = [ho.human_action for ho in step.human_options if not ho.human_action.name in ["LRD", HC.name]]
        if len(possible_other_human_actions)>0 and random.random()<P_WRONG_ID:
            id_result = random.choice(possible_other_human_actions)
        else:
            id_result = HC
    else:
        lg.debug("ID failed...")
        id_result = IdResult.FAILED

    if id_result!=IdResult.FAILED:
        lg.debug(f"ID successful: {id_result}")
    
    return id_result

def MOCK_assess_human_action(result_id):
    lg.debug(f"Assessed Human action: {HC}")
    if result_id!=IdResult.NOT_NEEDED and result_id.name!="LRD" and not CM.Action.are_similar(result_id, HC):
        lg.debug("Robot was wrong about Human action...")
    return HC


##################
## SubFonctions ##
##################
def get_first_step(begin_step: ConM.Step):
    if len(begin_step.children)!=1:
        raise Exception("begin_step should only have 1 child.")
    first_step = begin_step.children[0]
    return first_step

def get_agents_before_step(step: ConM.Step):
    return step.from_pair.end_agents

def exec_over(step):
    return step.is_final

def wait_step_start(step: ConM.Step):
    # i.e. wait for human to start acting
    lg.debug("\nCurrent step:")
    lg.debug(CM.str_agents(get_agents_before_step(step)))
    lg.debug(step.str())
    lg.debug("Waiting for human to act...")
    if not DEBUG:
        if INPUT:
            input()

def is_ID_needed(step: ConM.Step):
    # Only with best robot choice not a CRA
    return True

def ID_successful(result: CM.Action | None):
    return result!=IdResult.FAILED and result!=IdResult.NOT_NEEDED

def pick_best_valid_RA(step: ConM.Step, human_action: CM.Action):
    for ho in step.human_options:
        if ho.human_action==human_action:
            return ho.getBestPair().robot_action
    raise Exception("No best robot action defined...")

def pick_valid_passive(step: ConM.Step):
    for ho in step.human_options:
        for p in ho.action_pairs:
            if p.robot_action.is_passive():
                return p.robot_action

    raise Exception("Didn't find passive action for failed ID...")

def wait_step_end():
    lg.debug("Waiting step end...")
    if not DEBUG:
        if INPUT:
            input()

def get_executed_pair(step: ConM.Step, HA: CM.Action, RA: CM.Action):
    for ho in step.human_options:
        if CM.Action.are_similar(ho.human_action,HA):
            human_option = ho
            break
    pair = None
    for p in human_option.action_pairs:
        if CM.Action.are_similar(p.robot_action,RA):
            pair = p
            break
    if pair==None:
        raise WrongException("Wrong Human action identified and a conflict occured... (No corresponding parallel pair to recover).")
    return pair

def get_next_step(step: ConM.Step, HA: CM.Action, RA: CM.Action):
    executed_pair = get_executed_pair(step, HA, RA)
    first_next_pair = executed_pair.next[0]
    return first_next_pair.get_in_step()

def get_lrd_probas(nb_human_actions):
    if nb_human_actions<=1:
        raise Exception("nb_human_actions MUST BE > 1. There must be at least one HA and LRD.")

    not_eq_p = 0.0
    n = nb_human_actions+1
    if P_LET_ROBOT_DECIDE != -1:
        not_eq_p += P_LET_ROBOT_DECIDE
        n-=1
    if P_LEAVE_ROBOT_DO != -1:
        not_eq_p += P_LEAVE_ROBOT_DO
        n-=1

    p_eq = (1 - not_eq_p)/n
    p_lrde = p_eq if P_LET_ROBOT_DECIDE==-1 else P_LET_ROBOT_DECIDE
    p_lrdo = p_eq if P_LEAVE_ROBOT_DO==-1 else P_LEAVE_ROBOT_DO

    return p_lrde, p_lrdo, p_eq

def convert_rank_to_score(rank, nb):
    return -1/(nb-1) * rank + nb/(nb-1)
    return rank

##########
## MAIN ##
##########
def show_solution_exec():
    ConM.render_tree(begin_step)

def main_exec(domain_name, solution_tree, begin_step,r_p,h_p, r_ranked_leaves, h_ranked_leaves):
    global P_SUCCESS_ID_PHASE, P_WRONG_ID, HUMAN_TYPE, HUMAN_UPDATING, P_LET_ROBOT_DECIDE, P_LEAVE_ROBOT_DO

    # Mock ID phase
    P_SUCCESS_ID_PHASE  = 1.0
    P_WRONG_ID          = 0.0

    # Mock human behavior 
    #   "POLICY"  => 
    #   "RANDOM"  => Act randomly
    HUMAN_TYPE = "POLICY"
    HUMAN_UPDATING = False

    # Proba for random human(set to -1 to make it equiprobable) (must have P_LRDe + P_LRDo <= 1)
    P_LEAVE_ROBOT_DO    = -1
    P_LET_ROBOT_DECIDE  = -1

    # Init Seed
    seed = random.randrange(sys.maxsize)
    random.seed(seed)
    lg.debug(f"\nSeed was: {seed}")

    initDomain()

    if INPUT:
        print("Press Enter to start...")
        input()

    try:
        id,r_rank,h_rank, r_ranked_leaves, h_ranked_leaves = execution_simulation(begin_step,r_p,h_p, r_ranked_leaves, h_ranked_leaves)
        nb_sol = len(begin_step.get_final_leaves())
        # print(r_rank,h_rank,nb_sol)
        r_score = convert_rank_to_score(r_rank,nb_sol)
        h_score = convert_rank_to_score(h_rank,nb_sol)
        return (id,r_score,h_score, seed, r_ranked_leaves, h_ranked_leaves)
    except WrongException as inst:
        lg.debug(f"Exception catched: {inst.args[0]}")
        return (-1, seed)

def find_r_rank_of_id(steps, id):
    for s in steps:
        if s.id == id:
            return s.get_f_leaf().branch_rank_r

if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    domain_name, solution_tree, begin_step = load_solution()


    # ALIGNED #
    # r_criteria = [
    #     ("TimeEndHumanDuty",    False),
    #     ("HumanEffort",         False),
    #     ("TimeTaskCompletion",  False),
    #     ("GlobalEffort",        False),
    #     # ("RiskConflict",      False),
    # ]
    # h_criteria = [
    #     ("TimeEndHumanDuty",    False),
    #     ("HumanEffort",         False),
    #     ("TimeTaskCompletion",  False),
    #     ("GlobalEffort",        False),
    #     # ("RiskConflict",      False),
    # ]
    # EFFORT OPPO #
    # r_criteria = [
    #     ("TimeEndHumanDuty",    False),
    #     ("HumanEffort",         False),
    #     ("TimeTaskCompletion",  False),
    #     ("GlobalEffort",        False),
    #     # ("RiskConflict",      False),
    # ]
    # h_criteria = [
    #     ("TimeEndHumanDuty",    False),
    #     ("HumanEffort",         True),
    #     ("TimeTaskCompletion",  False),
    #     ("GlobalEffort",        True),
    #     # ("RiskConflict",      False),
    # ]
    # OPPO #
    # r_criteria = [
    #     ("TimeEndHumanDuty",    False),
    #     ("HumanEffort",         False),
    #     ("TimeTaskCompletion",  False),
    #     ("GlobalEffort",        False),
    #     # ("RiskConflict",      False),
    # ]
    # h_criteria = [
    #     ("TimeEndHumanDuty",    True),
    #     ("HumanEffort",         True),
    #     ("TimeTaskCompletion",  True),
    #     ("GlobalEffort",        True),
    #     # ("RiskConflict",      False),
    # ]

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


