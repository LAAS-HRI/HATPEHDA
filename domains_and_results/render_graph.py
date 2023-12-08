import dill
import graphviz
import sys
import time

import CommonModule as CM
import ConcurrentModule as ConM



def load(filename):

    print(f"Loading solution '{filename}' ... ", end="", flush=True)
    s_t = time.time()

    domain_name, init_step = dill.load(open(CM.path + filename, "rb"))

    print("Loaded! - %.2fs" %(time.time()-s_t))

    return domain_name, init_step


def load_solution():
    """
    Loads the previously produced solution.
    The domain name is retreived and returned and as well as the solution tree and the initial step.
    """

    filename = "dom_n_sol_with_choices.p"
    if len(sys.argv)>1:
        filename = sys.argv[1]

    return load(filename)


def action_gui_str(action: CM.Action, show_id=False):
    task_name = action.name if action.name!="PASSIVE" else "P"
    base_str = f"{task_name}{action.parameters}"

    id_str = ""
    if show_id:
        id_str = f"{action.id}-"

    return id_str + base_str

G_METRICS = False
def render_dot_new(init_step: ConM.Step, max_depth=None, ignored_step_ids=[], show_only={}, show_only_branch=None, pdf=False, show_optimal=False, with_next_step=False):
    global g_opti_branch_id
    format_file = "svg" if not pdf else "pdf"
    g = graphviz.Digraph('G', filename='render_dot.gv', format=format_file, 
        engine="dot",
        # engine="neato",
        graph_attr=dict(splines='true',
                        sep='5',
                        nslimit='2',
                        nslimit1='2',
                        overlap='scale'),
    )
    g.attr(compound='true')

    if show_only_branch!=None:
        max_depth=None
        ignored_step_ids=[]
        show_only={}

    # g.edge_attr["minlen"]="2"

    steps_to_render = [init_step]

    begin_node_name=""

    i_cluster=0
    while steps_to_render!=[]:
        s = steps_to_render.pop(0)

        if show_only_branch!=None and not show_only_branch in [leaf.id for leaf in s.get_final_leaves()]:
            continue
        if max_depth!=None and s.depth>max_depth:
            continue
        if s.depth in show_only and show_only[s.depth]!=s.id:
            continue
        if s.id in ignored_step_ids:
            continue

        if s.is_root:
            begin_node_name = s.human_options[0].action_pairs[0].get_short_str()
            g.node(begin_node_name, shape='circle', style="filled", color="black", label="", width="0.2", fixedsize="true")
        elif s.is_final():
            metrics_str = ""
            if s.parent.getBestPair()!=None:
                for m in s.human_options[0].action_pairs[0].branch_metrics.values():
                    metrics_str +=  f"-" if not metrics_str=="" else "\n"
                    metrics_str += format(m, ".3g")
                metrics_str += f"\n#{s.get_f_leaf().getBestRank()}"
            name = "f_"+s.human_options[0].action_pairs[0].get_short_str()
            g.node(name, shape='doublecircle', style="filled", color="black", label="", xlabel="("+str(s.id)+")"+metrics_str, width="0.2", fixedsize="true")
            if s.from_pair!=None:
                g.edge(str(s.from_pair.get_short_str()), name)
        else:
            name_step_cluster = f"cluster_{i_cluster}"
            one_node=""
            with g.subgraph(name=name_step_cluster) as cs:
                i_cluster+=1
                cs.attr(style='solid', bgcolor="#f3f3f3", label=f"{s.depth}-Step{s.get_str(with_bold=False)}")
                for ho in s.human_options:
                    with cs.subgraph(name=f"cluster_{i_cluster}") as c:
                        i_cluster+=1
                        h_label = action_gui_str(ho.human_action)
                        if s.getBestPair()!=None and CM.Action.are_similar(ho.human_action, s.getBestPair().human_action):
                            # h_label= '< <B>#' + h_label + '#</B> >'
                            h_label= '#' + h_label + '#'
                        c.attr(label=h_label, style='rounded', color="#D6B656", bgcolor="#FFE6CC")
                        
                        for p in ho.action_pairs:
                            node_name = p.get_short_str()

                            # Style
                            if p.robot_action.name=="SKIP" or ConM.check_list(s.CRA, lambda x: CM.Action.are_similar(x, p.robot_action)):
                                style="filled,bold,rounded"
                            elif p.robot_action.is_passive():
                                style = "filled,solid,rounded"
                            else:
                                style = "filled,solid,rounded"

                            # Shape
                            shape = "ellipse"
                            if p.robot_action.is_passive():
                                shape = "box"

                            r_label=action_gui_str(p.robot_action)
                            
                            if p.in_human_option.getBestPair()!=None and p==p.in_human_option.getBestPair():
                                # r_label = '''< <table border="0"><tr><td align="text">By default, td text is center-aligned<br align="right" /></td></tr></table> >'''
                                # r_label= '< <B>#' + r_label + '#</B> >'
                                r_label= '#' + r_label + '#'
                            if with_next_step and len(p.next):
                                r_label += f"\n({p.next[0].get_in_step().id})"

                            c.node(node_name, label=r_label, shape=shape, style=style, color="#6C8EBF", fillcolor="#DAE8FC")

                            if one_node=="":
                                one_node=node_name

            if s.from_pair!=None:
                if s.from_pair.get_in_step().is_root:
                    g.edge(str(s.from_pair.get_short_str()), one_node, lhead=name_step_cluster, minlen="2")
                else:
                    g.edge(str(s.from_pair.get_short_str()), one_node, lhead=name_step_cluster)

        if show_optimal:
            for child in s.children:
                if s.is_root or child.from_pair == s.getBestPair():
                    steps_to_render += [child]
            if len(s.children)==0:
                g_opti_branch_id = s.id
        else:
            steps_to_render += [child for child in s.children]

    g.view()

if __name__ == "__main__":

    domain_name, begin_step = load_solution()

    # Policy to use :
    # ConM.setPolicyName("human_min_work")
    ConM.setPolicyName("task_end_early")

    print("policy name: ", ConM.G_POLICY_NAME)

    max_depth = None
    ignored_steps_ids = []
    show_only = {}
    g_opti_branch_id = -1
    while True:
        print(" ")
        print("0) Render")
        print("1) Set max depth")
        print("2) Set ignored steps")
        print("3) Set show only")
        print("4) Explore")
        print("5) Show only branch id")
        print("6) Reset")
        print("7) Set Criteria")
        print("8) Render pdf")
        print("9) Render optimal plan")
        print("10) Switch policy")
        print("Choice: ", end="")
        choice = input()

        if choice=="0":
            render_dot_new(begin_step, max_depth=max_depth, ignored_step_ids=ignored_steps_ids, show_only=show_only)

        elif choice=="1":
            show_only_branch=None
            print("Current max depth: ", max_depth)
            print("Enter new max depth (d | r): ", end="")
            choice = input()
            if choice=="r":
                max_depth = None
            else:
                max_depth = int(choice)
            print(f"New max depth {max_depth}")

        elif choice=="2":
            show_only_branch=None
            print("Current ignored steps: ", ignored_steps_ids)
            print("Enter new ignored steps: ", end="")
            choice = input()
            if choice=="":
                ignored_steps_ids=[]
            else:
                choice = choice.replace(" ", "")
                choice = choice.split(",")
                ignored_steps_ids = [int(id) for id in choice]
            print(f"New ignored steps: {ignored_steps_ids}")

        elif choice=="3":
            show_only_branch=None
            print("Current show only: ", show_only)
            print("Enter new show only (depth, id | r): ", end="")
            choice = input()
            if choice=="":
                show_only={}
            else:
                choice = choice.replace(" ", "")
                choice = choice.split(",")
                depth = int(choice[0])
                id = choice[1]
                if id=="r":
                    show_only.pop(depth)
                else:
                    id = int(id)
                    show_only[depth] = id
            print(f"New show_only: {show_only}")

        elif choice=="4":
            show_only_branch=None
            explo_depth = 1
            explo_show_only = {}
            explo_show_only[explo_depth] = 1
            render_dot_new(begin_step, max_depth=explo_depth, show_only=explo_show_only, with_next_step=True)

            choice = None
            while choice!="q":
                print("Enter step to explore (id | s | r | q): ", end="")
                choice = input()

                if choice=="s":
                    max_depth = explo_depth
                    show_only = explo_show_only
                
                elif choice=="r":
                    explo_show_only.pop(explo_depth)
                    explo_depth -= 1
                    render_dot_new(begin_step, max_depth=explo_depth, show_only=explo_show_only, with_next_step=True)

                elif choice!="q":
                    explo_depth += 1
                    explo_show_only[explo_depth] = int(choice) 
                    render_dot_new(begin_step, max_depth=explo_depth, show_only=explo_show_only, with_next_step=True)

        elif choice=="5":
            print("Enter id branch: ", end="")
            choice = int(input())
            show_only_branch = choice
            render_dot_new(begin_step, show_only_branch=choice)

        elif choice=="6":
            show_only_branch=None
            max_depth = None
            ignored_steps_ids = []
            show_only = {}

        elif choice=="7":
            pass

        elif choice=="8":
            render_dot_new(begin_step, max_depth=max_depth, ignored_step_ids=ignored_steps_ids, show_only=show_only, show_only_branch=show_only_branch, pdf=True)

        elif choice=="9":
            render_dot_new(begin_step, show_optimal=True)
            show_only_branch = g_opti_branch_id

        elif choice=="10":
            policies = ["task_end_early", "human_min_work"]
            new_policy = input(f"1) {policies[0]}\n2) {policies[1]}\nNew policy : ")
            if new_policy in [1,2]:
                ConM.setPolicyName(policies[new_policy-1])
            else:
                print("Unknown policy name...")





        