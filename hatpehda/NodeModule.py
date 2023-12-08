from enum import Enum
from typing import Any, Dict
import sys
sys.path.append("/home/afavier/ws/HATPEHDA/hatpehda")


import CommonModule as CM
import NodeModule as NM

class Node:
    __ID = 0
    def __init__(self):
        Node.__ID += 1
        self.id = Node.__ID
        self.__type = None
        self.__flag = None
        self.start_action = None
        self.end_action = None
        self.previous_node = None
        self.next_nodes = []
        self.start_agents = None
        self.end_agents = None
        self.length = 1
        self.cost = 0.0
        self.fcost = 0.0
        self.selected_next = ""
        self.depth = 0
        self.best_metrics = None
        self.has_been_delayed_with = None
        self.delayed_from = None

    class Type(Enum):
        R = 0 # Robot choice
        H = 1 # Human choice
        F = 2 # Final
        I = 3 # Incomplete
        D = 4 # Robot delaying action
    
    class Flag(Enum):
        F = 0 # Finished
        E = 1 # To explore
        U = 2 # More expensive than current solution
        S = 3 # Solution
        D = 4 # Deadlock 

    @property
    def type(self):
        return self.__type
    @type.setter
    def type(self, value):
        if value in Node.Type:
            self.__type = value
        else:
            raise Exception("Error while setting the type of a Node. '{}' isn't a valid type!".format(value))
    
    @property
    def flag(self):
        return self.__flag
    @flag.setter
    def flag(self, value):
        if value in Node.Flag:
            self.__flag = value
        else:
            raise Exception("Error while setting the flag of a Node. '{}' isn't a valid flag!".format(value))
    
    def __repr__(self):
        next_str = ""
        for n in self.next_nodes:
            if next_str!="":
                next_str += " "
            next_str += "#{}".format(n.id)
        prev_str = "None" if self.previous_node==None else "#{}".format(self.previous_node.id)
        return "{} {} {}#{}, ({} {} {}) -{}> ({} {} {}) prev={} next=[{}]".format(self.cost, self.flag, self.type, self.id, self.start_action.agent, self.start_action.name, self.start_action.parameters, self.length, self.end_action.agent, self.end_action.name, self.end_action.parameters, prev_str, next_str)

    def show(self):
        print(self)
    
    def get_last_nodes(self):
        last_nodes=[]

        if self.next_nodes==[]:
            return [self]

        for next in self.next_nodes:
            last_nodes += next.get_last_nodes()

        return last_nodes

    def get_first_node(self):
        n = self
        while n.previous_node!=None:
            n = n.previous_node
        return n

    def compute_fcost(self):
        fcost = None
        i = None
        if self.type==Node.Type.F or self.type==Node.Type.I or self.type==Node.Type.D:
            fcost = self.cost
        elif self.type==Node.Type.R:
            next_costs = []
            for next in self.next_nodes:
                next_costs.append(next.compute_fcost()[0])
            fcost = min(next_costs)
            i = min(range(len(next_costs)), key=next_costs.__getitem__)
            self.selected_next = self.next_nodes[i].id
        elif self.type==Node.Type.H:
            total = 0
            for next in self.next_nodes:
                total += next.compute_fcost()[0]
            fcost = total/len(self.next_nodes)
        self.fcost = fcost
        return (fcost, i)

def get_last_nodes_action(first_node):
        last_actions=[]

        if first_node.next_nodes==[]:
            return [first_node.end_action]

        for next in first_node.next_nodes:
            last_actions += get_last_nodes_action(next)

        return last_actions

def createFirstNode(agents, begin_action):
    begin_action.branching_name = "origin"
    node = Node()
    node.start_agents = agents
    node.end_agents = agents
    node.start_action = begin_action
    node.end_action = begin_action
    node.cost = begin_action.cost
    node.flag = Node.Flag.E
    node.type = Node.Type.I
    return node

def pick_cheapest_node(nodes):
    if len(nodes) == 0:
        return None

    min_cost = nodes[0].cost
    min_i = 0
    for i, n in enumerate(nodes[1:], start=1):
        if n.cost < min_cost:
            min_cost = n.cost
            min_i = i

    return nodes[min_i]

def pick_cheapest_final_node(nodes):
    if len(nodes) == 0:
        return None

    min_f_i = -1
    min_f_cost = -1
    for i, n in enumerate(nodes):
        if n.type == Node.Type.F:
            if min_f_i == -1:
                min_f_i = i
                min_f_cost = n.cost
            elif n.cost < min_f_cost:
                min_f_i = i
                min_f_cost = n.cost
    
    if min_f_i != -1:
        return nodes[min_f_i]
    else: # None of the nodes are final 
        return None

def create_incomplete_node_dec(decomp, previous_node, cost, depth):
    node = Node()
    action = decomp.subtasks[0]
    dec_agents = decomp.agents
    node.start_agents = dec_agents
    node.end_agents = dec_agents
    node.start_action = action
    node.end_action = action
    node.cost = action.cost
    node.flag = Node.Flag.E
    node.type = Node.Type.I
    node.previous_node = previous_node
    node.cost = cost
    node.depth = depth
    return node

def show_node(node):
    if node!=None:
        node.show()
    else:
        print("None")

def show_nodes(nodes):
    for n in nodes:
        print("\t", end="")
        show_node(n)

def get_plans(first_node):
    last_actions = get_last_nodes_action(first_node)
    plans = []
    for a in last_actions:
        plan = []
        while a.previous != None:
            plan.append(a)
            a = a.previous
        plans.append(plan)
    
    return plans

def get_plans_str(first_node):
    plans = get_plans(first_node)

    plans_str = ""
    for plan in plans:
        plan_str=""
        for i in range(len(plan)-1,-1,-1):
            plan_str += " "+str(plan[i]) if plan_str!="" else str(plan[i])
        plans_str += "/"+plan_str if plans_str!="" else plan_str
    
    return plans_str

def show_plans_str(first_node):
    print("Plans:\n{}".format(get_plans_str(first_node)))

def compute_metrics_trace(last_action):
    nb_com = 0
    nb_h_wait = 0
    length = 0
    nb_delay = 0

    a = last_action
    while a.name != "BEGIN":
        length +=1
        if a.name=="COM_ALIGN":
            nb_com += 1
            length -=1
        if a.name=="WAIT" and a.agent == "human":
            nb_h_wait += 1
        if a.name=="DELAY":
            nb_delay += 1
        a = a.previous

    return (nb_com, nb_h_wait, length, nb_delay)

def compare_metrics(metrics):
    best_metric = metrics[0]
    i_best = 0
    for i, m in enumerate(metrics[1:]):
        if m[0] > best_metric[0]:
            pass
        elif m[0] < best_metric[0] and m[1] <= best_metric[1]:
            best_metric = m
            i_best = i+1
        else:
            if m[1] < best_metric[1]:
                best_metric = m
                i_best = i+1
            elif m[1] == best_metric[1]:
                if m[2] < best_metric[2]:
                    best_metric = m

    # returns best metrics
    return metrics[i_best]

def compute_node_metrics(node):
    if Node.Type.H == node.type:
        # compute average of children metrics
        a = 0
        b = 0
        c = 0
        d = 0
        for n in node.next_nodes:
            compute_node_metrics(n)
            a += n.best_metrics[0]
            b += n.best_metrics[1]
            c += n.best_metrics[2]
            d += n.best_metrics[3]
        a/=len(node.next_nodes)
        b/=len(node.next_nodes)
        c/=len(node.next_nodes)
        d/=len(node.next_nodes)
        node.best_metrics = (a,b,c,d)

    elif Node.Type.R == node.type:
        # take best children metrics
        metrics = []
        for n in node.next_nodes:
            compute_node_metrics(n)
            metrics.append(n.best_metrics)
        node.best_metrics = compare_metrics(metrics)

    elif Node.Type.F == node.type:
        node.best_metrics = compute_metrics_trace(get_last_nodes_action(node)[0])

    else:
        raise Exception("compute_node_metrics: Node type not supported...")
    
def get_best_traces(node):
    # compute_node_metrics(first_node)

    best = []

    if Node.Type.H == node.type:
        for n in node.next_nodes:
            best += get_best_traces(n)
    elif Node.Type.R == node.type:
        for n in node.next_nodes:
            if n.best_metrics == node.best_metrics:
                best += get_best_traces(n)
                break
    elif Node.Type.F == node.type:
        best = get_last_nodes_action(node) # list of one action 
    else:
        raise Exception("get_best_traces: Node type not supported...")
    
    return best

def filter_delay_traces(node):
    if node.type == Node.Type.H:
        for n in node.next_nodes:
            filter_delay_traces(n)
    if node.type == Node.Type.R:
        repeat = True
        while repeat:
            repeat =False
            for n in node.next_nodes:
                if n.has_been_delayed_with!=None:
                    delay_node = None
                    for m in node.next_nodes:
                        if m.id == n.has_been_delayed_with:
                            delay_node = m
                            break
                    if delay_node.best_metrics[1] > n.best_metrics[1]:
                        repeat = True
                        n.has_been_delayed_with = None
                        node.next_nodes.remove(m)
    if node.type == Node.Type.F:
        pass

########################

def filter(node):
    if node.type == Node.Type.R:
        for nn in node.next_nodes:
            if nn.id == node.selected_next:
                node.next_nodes = [nn]
        node.end_action.next = [ node.next_nodes[0].start_action ]
    for next_node in node.next_nodes:
        filter(next_node)

def show_plans_str_selection(first_node):

    filter(first_node)

    last_actions = get_last_nodes_action(first_node)
    plans = []
    for a in last_actions:
        plan = []
        while a.previous != None:
            plan.append(a)
            a = a.previous
        plans.append(plan)

    plans_str = ""
    for plan in plans:
        plan_str=""
        for i in range(len(plan)-1,-1,-1):
            plan_str += " "+str(plan[i]) if plan_str!="" else str(plan[i])
        plans_str += "/"+plan_str if plans_str!="" else plan_str
    
    print("Filtered Plans:\n{}".format(plans_str))

def compare_states(state1, state2):
    # print("inside compare")
    for fluent_name in state1.fluent_names:
        f1 = state1.get_fluent(fluent_name)
        f2 = state2.get_fluent(fluent_name)
        if f1.is_dyn and f2.is_dyn:
            # print("f1={}-{} f2={}-{}".format(f1.name, f1.val, f2.name, f2.val))
            if f1.val != f2.val:
                return False
    return True

def show_belief_alignmen(first_node):
    diff = False

    last_nodes = first_node.get_last_nodes()

    for node in last_nodes:
        # print("check node")
        if not compare_states(node.end_agents[CM.g_robot_name].state, node.end_agents[CM.g_human_name].state):
            # print("diff")
            diff = True
            # break
        # else:
        #     print("no diff")

    print("Non relevant div:\n{}".format(diff))    
