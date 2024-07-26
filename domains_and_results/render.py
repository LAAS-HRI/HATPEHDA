import dill
import graphviz
import sys
import time

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

    filename = "policy.p"
    if len(sys.argv)>1:
        filename = sys.argv[1]

    return load(filename)

def compute_action_pair_label(action_pair, with_rank=False):

    if action_pair.human_action.is_idle():
        ha = "IDLE"
    elif action_pair.human_action.is_wait():
        ha = "WAIT"
    elif action_pair.human_action.is_passive():
        ha = "PASS"
    else:
        ha = f"{action_pair.human_action.name}{action_pair.human_action.parameters}"

    if action_pair.robot_action.is_idle():
        ra = "IDLE"
    elif action_pair.robot_action.is_wait():
        ra = "WAIT"
    elif action_pair.robot_action.is_passive():
        ra = "PASS"
    else:
        ra = f"{action_pair.robot_action.name}{action_pair.robot_action.parameters}"

    s = f"H: {ha}\nR: {ra}"
    if with_rank:
        s += f" [{action_pair.rank}]"
    return s

def compute_action_pair_name(pair):
    return f"{pair.human_action.id}-{pair.robot_action.id}"

###########################

def render_new_sol(show_pstate_id=False, show_pair_rank=False):
    global g_opti_branch_id
    g = graphviz.Digraph('G', filename='render_dot.gv', format="svg", 
        engine="dot",
        # engine="neato",
        graph_attr=dict(splines='true',
                        sep='5',
                        nslimit='2',
                        nslimit1='2',
                        overlap='scale'),
    )
    g.attr(compound='true')

    ipstates_to_render = {0}
    ipstates_rendered = set()

    while len(ipstates_to_render)!=0:
        ips = ipstates_to_render.pop() 
        over = False
        while ips in ipstates_rendered:
            if len(ipstates_to_render)>0:
                ips = ipstates_to_render.pop()
            else:
                over = True
                break
        if over:
            break

        ps = CM.g_PSTATES[ips]

        # check if last
        if ps.children==[] and ps.id in CM.g_FINAL_IPSTATES:
            g.node(str(ps.id), shape='doublecircle', style="filled", color="black", label="", xlabel="("+str(ps.id)+")", width="0.2", fixedsize="true")

        # check if first
        else:
            if ps.id==0:
                g.node(str(ps.id), shape='circle', style='filled', color='black', label='', width="0.2", fixedsize="true")
            else:
                if show_pstate_id:
                    g.node(str(ps.id), shape='ellipse', style='filled', fillcolor='white')
                else:
                    g.node(str(ps.id), shape='circle', style='filled', fillcolor='white', label='', width='0.15', fixedsize="true")

            for c in ps.children:

                if c.child!=None:

                    action_pair_node_name = compute_action_pair_name(c)
                    g.edge(str(ps.id), action_pair_node_name)
                    if c.best:
                        node_style = "rounded,filled"
                        node_fillcolor = "gold"
                        g.node(action_pair_node_name, label=compute_action_pair_label(c, with_rank=show_pair_rank), shape="box", style=node_style, fillcolor=node_fillcolor)
                    else:
                        g.node(action_pair_node_name, label=compute_action_pair_label(c, with_rank=show_pair_rank), shape="box")
                    g.edge(action_pair_node_name, str(c.child))
                    ipstates_to_render = ipstates_to_render.union({c.child})

        ipstates_rendered = ipstates_rendered.union({ps.id})

    g.view()

def render_policy(show_pstate_id=False, show_pair_rank=False):
    global g_opti_branch_id
    g = graphviz.Digraph('G', filename='render_dot.gv', format="svg", 
        engine="dot",
        # engine="neato",
        graph_attr=dict(splines='true',
                        sep='5',
                        nslimit='2',
                        nslimit1='2',
                        overlap='scale'),
    )
    g.attr(compound='true')

    ipstates_to_render = {0}
    ipstates_rendered = set()

    while len(ipstates_to_render)!=0:
        ips = ipstates_to_render.pop() 
        over = False
        while ips in ipstates_rendered:
            if len(ipstates_to_render)>0:
                ips = ipstates_to_render.pop()
            else:
                over = True
                break
        if over:
            break

        ps = CM.g_PSTATES[ips]

        # check if last
        if ps.children==[]:
            g.node(str(ps.id), shape='doublecircle', style="filled", color="black", label="", xlabel="("+str(ps.id)+")", width="0.2", fixedsize="true")

        # check if first
        else:
            if ps.id==0:
                g.node(str(ps.id), shape='circle', style='filled', color='black', label='', width="0.2", fixedsize="true")
            else:
                if show_pstate_id:
                    g.node(str(ps.id), shape='ellipse', style='filled', fillcolor='white')
                else:
                    g.node(str(ps.id), shape='circle', style='filled', fillcolor='white', label='', width='0.15', fixedsize="true")

            for c in ps.children:

                if c.best_compliant and c.child!=None:
                    action_pair_node_name = compute_action_pair_name(c)

                    arrowhead = "normal" 
                    arrowsize = "1.0" 
                    node_style = ""
                    node_fillcolor = "lightgrey"
                    if c.best:
                        # arrowhead = "diamond" 
                        # arrowsize = "2.0" 
                        node_style = "rounded,filled"
                        node_fillcolor = "gold"

                    g.edge(str(ps.id), action_pair_node_name, arrowhead=arrowhead, arrowsize=arrowsize)
                    g.node(action_pair_node_name, label=compute_action_pair_label(c, with_rank=show_pair_rank), shape="box", style=node_style, fillcolor=node_fillcolor)
                    g.edge(action_pair_node_name, str(c.child), arrowhead=arrowhead, arrowsize=arrowsize)

                    ipstates_to_render = ipstates_to_render.union({c.child})

        ipstates_rendered = ipstates_rendered.union({ps.id})

    g.view()

def render_simple():
    global g_opti_branch_id
    s = '0.1'
    ar_size = '0.4'
    g = graphviz.Digraph('G', filename='render_dot.gv', format="svg", 
        engine="dot",
        # engine="neato",
        graph_attr=dict(splines='true',
                        sep='5',
                        nodesep=s,
                        ranksep=s,
                        nslimit='2',
                        nslimit1='2',
                        overlap='scale',
                        ),
    )
    g.attr(compound='true')

    ipstates_to_render = {0}
    ipstates_rendered = set()

    while len(ipstates_to_render)!=0:
        ips = ipstates_to_render.pop() 
        over = False
        while ips in ipstates_rendered:
            if len(ipstates_to_render)>0:
                ips = ipstates_to_render.pop()
            else:
                over = True
                break
        if over:
            break

        ps = CM.g_PSTATES[ips]

        # check if last
        if ps.children==[]:
            g.node(str(ps.id), shape='doublecircle', style="filled", color="black", label="", xlabel="("+str(ps.id)+")", width="0.2", fixedsize="true")

        # check if first
        else:
            if ps.id==0:
                g.node(str(ps.id), shape='circle', style='filled', color='black', label='', width="0.2", fixedsize="true")
            else:
                g.node(str(ps.id), shape='circle', style='filled', fillcolor='white', label='', width="0.15", fixedsize="true")

            for c in ps.children:

                if c.child!=None:

                    action_pair_node_name = compute_action_pair_name(c)
                    g.edge(str(ps.id), action_pair_node_name, arrowsize=ar_size)
                    g.node(action_pair_node_name, label='', shape="box", width="0.1", height="0.1", fixedsize="true")

                    g.edge(action_pair_node_name, str(c.child), arrowsize=ar_size)
                    ipstates_to_render = ipstates_to_render.union({c.child})

        ipstates_rendered = ipstates_rendered.union({ps.id})

    g.view()

def render_generation_step(to_merge,to_propagate,filename='render_dot.gv'):
    global g_opti_branch_id
    s = '0.1'
    ar_size = '0.4'
    g = graphviz.Digraph('G', filename=filename, format="svg", 
        engine="dot",
        # engine="neato",
        graph_attr=dict(splines='true',
                        sep='5',
                        nodesep=s,
                        ranksep=s,
                        nslimit='2',
                        nslimit1='2',
                        overlap='scale',
                        ),
    )
    g.attr(compound='true')

    ipstates_to_render = {0}
    ipstates_rendered = set()

    while len(ipstates_to_render)!=0:
        ips = ipstates_to_render.pop() 
        over = False
        while ips in ipstates_rendered:
            if len(ipstates_to_render)>0:
                ips = ipstates_to_render.pop()
            else:
                over = True
                break
        if over:
            break

        ps = CM.g_PSTATES[ips]

        color = "white" if ps.best_metrics==None else "red"

        # check if last
        if ps.children==[]:
            g.node(str(ps.id), shape='doublecircle', style="filled", fillcolor=color, label="", xlabel="("+str(ps.id)+")", width="0.2", fixedsize="true")

        # check if first
        else:
            if ps.id==0:
                g.node(str(ps.id), shape='circle', style='filled', fillcolor=color, label='', width="0.2", fixedsize="true")
            else:
                g.node(str(ps.id), shape='circle', style="filled", label='', fillcolor=color, width="0.15", fixedsize="true")

            for c in ps.children:

                if c.child!=None:

                    action_pair_node_name = compute_action_pair_name(c)
                    g.edge(str(ps.id), action_pair_node_name, arrowsize=ar_size)
                    pair_color = "white" if c.best_metrics==None else "red"
                    pair_color = "chartreuse2" if c.best else pair_color
                    g.node(action_pair_node_name, label='', shape="box", style="filled", fillcolor=pair_color, width="0.1", height="0.1", fixedsize="true")

                # if c.child!=None:
                    g.edge(action_pair_node_name, str(c.child), arrowsize=ar_size)
                    ipstates_to_render = ipstates_to_render.union({c.child})

        ipstates_rendered = ipstates_rendered.union({ps.id})

    # g.view()
    g.render()

def render_policy_simple():
    global g_opti_branch_id
    s = '0.1'
    ar_size = '0.4'
    g = graphviz.Digraph('G', filename='render_dot.gv', format="svg", 
        engine="dot",
        # engine="neato",
        graph_attr=dict(splines='true',
                        sep='5',
                        nodesep=s,
                        ranksep=s,
                        nslimit='2',
                        nslimit1='2',
                        overlap='scale',
                        ),
    )
    g.attr(compound='true')

    ipstates_to_render = {0}
    ipstates_rendered = set()

    while len(ipstates_to_render)!=0:
        ips = ipstates_to_render.pop() 
        over = False
        while ips in ipstates_rendered:
            if len(ipstates_to_render)>0:
                ips = ipstates_to_render.pop()
            else:
                over = True
                break
        if over:
            break

        ps = CM.g_PSTATES[ips]

        # check if last
        if ps.children==[]:
            g.node(str(ps.id), shape='doublecircle', style="filled", color="black", label="", xlabel="("+str(ps.id)+")", width="0.2", fixedsize="true")

        # check if first
        else:
            if ps.id==0:
                g.node(str(ps.id), shape='circle', style='filled', color='black', label='', width="0.2", fixedsize="true")
            else:
                g.node(str(ps.id), shape='circle', label='', width="0.15", fixedsize="true")

            for c in ps.children:

                if c.best_compliant and c.child!=None:

                    action_pair_node_name = f"{c.human_action.id}-{c.robot_action.id}"
                    g.edge(str(ps.id), action_pair_node_name, arrowsize=ar_size)
                    g.node(action_pair_node_name, label='', shape="box", width="0.1", height="0.1", fixedsize="true")

                    g.edge(action_pair_node_name, str(c.child), arrowsize=ar_size)
                    ipstates_to_render = ipstates_to_render.union({c.child})

        ipstates_rendered = ipstates_rendered.union({ps.id})

    g.view()

def render_best_trace():
    g = graphviz.Digraph('G', filename='render_dot.gv', format="svg", 
        engine="dot",
        graph_attr=dict(splines='true',
                        sep='5',
                        nslimit='2',
                        nslimit1='2',
                        overlap='scale'),
    )
    g.attr(compound='true')

    ipstates_to_render = {0}
    ipstates_rendered = set()
    if CM.g_PSTATES[0].best_metrics!=None:
        print("Best metrics: ", CM.g_PSTATES[0].best_metrics)

    previous_pair_name = None

    while len(ipstates_to_render)!=0:
        ips = ipstates_to_render.pop() 
        over = False
        while ips in ipstates_rendered:
            if len(ipstates_to_render)>0:
                ips = ipstates_to_render.pop()
            else:
                over = True
                break
        if over:
            break

        ps = CM.g_PSTATES[ips]

        # check if last
        if ps.children==[]:
            g.node(str(ps.id), shape='doublecircle', style="filled", color="black", label="", xlabel="("+str(ps.id)+")", width="0.2", fixedsize="true")
            action_pair_node_name = compute_action_pair_name(ps.parents[0])
            g.edge(action_pair_node_name ,str(ps.id))

        else:
            # check if first, create node
            if ps.id==0:
                g.node(str(ps.id), shape='circle', style='filled', color='black', label='', width="0.2", fixedsize="true")

            for c in ps.children:

                if c.best:
                    action_pair_node_name = compute_action_pair_name(c)

                    # check if first pair, connect it to first node
                    if c.parent==0:
                        g.edge("0", action_pair_node_name)
                        previous_pair_name = action_pair_node_name
                    else:
                        g.edge( previous_pair_name, action_pair_node_name )

                    node_style = "rounded,filled"
                    node_fillcolor = "gold"

                    g.node(action_pair_node_name, label=compute_action_pair_label(c), shape="box", style=node_style, fillcolor=node_fillcolor)

                    ipstates_to_render = ipstates_to_render.union({c.child})

                    previous_pair_name = action_pair_node_name

        ipstates_rendered = ipstates_rendered.union({ps.id})

    g.view()

def render_leaf(leaf_id, show_pstate_id=False, show_only_policy=False, show_pair_rank=False):
    s = '0.2'
    g = graphviz.Digraph('G', filename='render_dot.gv', format="svg", 
        engine="dot",
        # engine="neato",
        graph_attr=dict(splines='true',
                        sep='5',
                        nodesep=s,
                        ranksep=s,
                        nslimit='2',
                        nslimit1='2',
                        overlap='scale',
                        ),
    )
    g.attr(compound='true')

    ipstates_to_render = {leaf_id}
    ipstates_rendered = set()

    while len(ipstates_to_render)!=0:
        ips = ipstates_to_render.pop() 
        over = False
        while ips in ipstates_rendered:
            if len(ipstates_to_render)>0:
                ips = ipstates_to_render.pop()
            else:
                over = True
                break
        if over:
            break

        ps = CM.g_PSTATES[ips]

        # check if first
        if ps.id==0:
            g.node(str(ps.id), shape='circle', style='filled', color='black', label='', width="0.2", fixedsize="true")
        else:
            # check if last
            if ps.children==[]:
                g.node(str(ps.id), shape='doublecircle', style="filled", color="black", label="", xlabel="("+str(ps.id)+")", width="0.2", fixedsize="true")
            else:
                if show_pstate_id:
                    g.node(str(ps.id), shape='ellipse', style='filled', fillcolor='white')
                else:
                    g.node(str(ps.id), shape='circle', style='filled', fillcolor='white', label='', width='0.15', fixedsize="true")

            for p in ps.parents:

                if (not show_only_policy) or (show_only_policy and p.best_compliant): 
                    action_pair_node_name = compute_action_pair_name(p)

                    arrowhead = "normal" 
                    arrowsize = "1.0" 
                    node_style = ""
                    node_fillcolor = "lightgrey"
                    if p.best:
                        # arrowhead = "diamond" 
                        # arrowsize = "2.0" 
                        node_style = "rounded,filled"
                        node_fillcolor = "gold"

                    g.edge(action_pair_node_name, str(ps.id), arrowhead=arrowhead, arrowsize=arrowsize)
                    g.node(action_pair_node_name, label=compute_action_pair_label(p, with_rank=show_pair_rank), shape="box", style=node_style, fillcolor=node_fillcolor)
                    g.edge(str(p.parent), action_pair_node_name, arrowhead=arrowhead, arrowsize=arrowsize)

                    ipstates_to_render = ipstates_to_render.union({p.parent})

        ipstates_rendered = ipstates_rendered.union({ps.id})

    g.view()

def explore():
    g = graphviz.Digraph('G', filename='render_dot.gv', format="svg", 
        engine="dot",
        # engine="neato",
        graph_attr=dict(splines='true',
                        sep='5',
                        nslimit='2',
                        nslimit1='2',
                        overlap='scale'),
    )
    g.attr(compound='true')

    ipstates_to_render = {0}
    ipstates_rendered = set()

    # RENDER
    while len(ipstates_to_render)!=0:
        ips = ipstates_to_render.pop() 
        over = False
        while ips in ipstates_rendered:
            if len(ipstates_to_render)>0:
                ips = ipstates_to_render.pop()
            else:
                over = True
                break
        if over:
            break

        ps = CM.g_PSTATES[ips]

        # check if last
        if ps.children==[] and ps.id in CM.g_FINAL_IPSTATES:
            g.node(str(ps.id), shape='doublecircle', style="filled", color="black", label="", xlabel="("+str(ps.id)+")", width="0.2", fixedsize="true")

        # check if first
        else:
            if ps.id==0:
                g.node(str(ps.id), shape='circle', style='filled', color='black', label='', width="0.2", fixedsize="true")
            else:
                if show_pstate_id:
                    g.node(str(ps.id), shape='circle', style='filled', fillcolor='white')
                else:
                    g.node(str(ps.id), shape='circle', style='filled', fillcolor='white', label='', width='0.15', fixedsize="true")

            for c in ps.children:

                if c.child!=None:

                    action_pair_node_name = compute_action_pair_name(c)
                    g.edge(str(ps.id), action_pair_node_name)
                    if c.best:
                        node_style = "rounded,filled"
                        node_fillcolor = "gold"
                        g.node(action_pair_node_name, label=compute_action_pair_label(c, with_rank=show_pair_rank), shape="box", style=node_style, fillcolor=node_fillcolor)
                    else:
                        g.node(action_pair_node_name, label=compute_action_pair_label(c, with_rank=show_pair_rank), shape="box")
                    g.edge(action_pair_node_name, str(c.child))

        ipstates_rendered = ipstates_rendered.union({ps.id})

    g.view()

    while True:
        print(" ")
        print("Enter id of to explore (-1 to quit): ", end="")
        choice = input()

        if choice=="-1":
            break
        else:
            # udpdate graph to show
            ipstates_to_render = ipstates_to_render.union({int(choice)})

            # RENDER
            while len(ipstates_to_render)!=0:
                ips = ipstates_to_render.pop() 
                over = False
                while ips in ipstates_rendered:
                    if len(ipstates_to_render)>0:
                        ips = ipstates_to_render.pop()
                    else:
                        over = True
                        break
                if over:
                    break

                ps = CM.g_PSTATES[ips]

                # check if last
                if ps.children==[] and ps.id in CM.g_FINAL_IPSTATES:
                    g.node(str(ps.id), shape='doublecircle', style="filled", color="black", label="", xlabel="("+str(ps.id)+")", width="0.2", fixedsize="true")

                # check if first
                else:
                    if ps.id==0:
                        g.node(str(ps.id), shape='circle', style='filled', color='black', label='', width="0.2", fixedsize="true")
                    else:
                        g.node(str(ps.id), shape='ellipse', style='filled', fillcolor='white')

                    for c in ps.children:

                        if c.child!=None:

                            action_pair_node_name = compute_action_pair_name(c)
                            g.edge(str(ps.id), action_pair_node_name)
                            if c.best:
                                node_style = "rounded,filled"
                                node_fillcolor = "gold"
                                g.node(action_pair_node_name, label=compute_action_pair_label(c, with_rank=show_pair_rank), shape="box", style=node_style, fillcolor=node_fillcolor)
                            else:
                                g.node(action_pair_node_name, label=compute_action_pair_label(c, with_rank=show_pair_rank), shape="box")
                            g.edge(action_pair_node_name, str(c.child))

                ipstates_rendered = ipstates_rendered.union({ps.id})

            g.view()


###########################

if __name__ == "__main__":

    sys.argv.append('policy_cart_pref1.p')    
    # sys.argv.append('search_space.p')    

    if len(sys.argv)<=1:
        raise Exception("Missing filename...")
    filename = sys.argv[1]

    CM.g_domain_name, CM.g_PSTATES, CM.g_FINAL_IPSTATES = load(filename)

    print(f"Number of leaves: {len(CM.g_FINAL_IPSTATES)}")
    print(f"Nb states = {len(CM.g_PSTATES)}")

    show_pstate_id = False
    show_pair_rank = False
        
    while True:
        print(" ")
        print("1) Full sol")
        print("2) Full sol (simplified)")
        print("3) Policy only")
        print("4) Policy only (simplified)")
        print("5) *Explore*")
        print("6) Best Trace")
        print("7) Show leaf")
        show_pstate_id_str = "Show" if not show_pstate_id else "Hide"
        print("8) " + show_pstate_id_str + " pstate id")
        show_pair_rank_str = "Show" if not show_pair_rank else "Hide"
        print("9) " + show_pair_rank_str + " pair rank")
        print("Choice: ", end="")
        choice = input()

        if choice=="1":
            render_new_sol(show_pstate_id=show_pstate_id, show_pair_rank=show_pair_rank)

        elif choice=="2":
            render_simple()

        elif choice=="3":
            render_policy(show_pstate_id=show_pstate_id, show_pair_rank=show_pair_rank)

        elif choice=="4":
            render_policy_simple()

        elif choice=="5":
            # print("not implemented...")
            explore()

        elif choice=="6":
            render_best_trace()

        elif choice=="7":
            while True:
                id = int(input("\tEnter leaf id to render: "))
                if not int(id) in CM.g_FINAL_IPSTATES:
                    print("ERROR")
                    continue
                show_only_policy = input("\tShow only policy from leaf? ( 1-yes 2-no ): ")
                if not show_only_policy in ["1","2"]:
                    print("ERROR")
                    continue
                show_only_policy = show_only_policy=="1"
                render_leaf(id,  show_pstate_id=show_pstate_id, show_only_policy=show_only_policy, show_pair_rank=show_pair_rank)
                break

        elif choice=="8":
            show_pstate_id = not show_pstate_id

        elif choice=="9":
            show_pair_rank = not show_pair_rank
