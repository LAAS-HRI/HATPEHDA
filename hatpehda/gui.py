from graphviz import Digraph
import os
import sys

sys.path.append("/home/afavier/ws/HATPEHDA/hatpehda")

import hatpehda

def show_plan(actions, controlable_agent, uncontrolable_agent, with_abstract=True):
    dot = Digraph(comment='Plan', format="png")
    dot.attr(fontsize="20")
    plotted_edge = set()

    for action in actions:
        while action is not None:
            color = "#A4C7FF" if action.agent == controlable_agent else "#FFDB9B"
            color_darker = "#5194FD" if action.agent == controlable_agent else "#FFBA40"
            shape = "octagon" if action.name == "IDLE" else "ellipse"
            dot.node(str(action.id), action.name + "\n(" + ",".join(map(lambda x: str(x), action.parameters)) + ")", style="filled", fillcolor=color, shape=shape)
            why = action.why
            how = action
            if with_abstract:
                while why is not None:
                    if (why.id, how.id) not in plotted_edge:
                        dot.node(str(why.id), why.name, shape="rectangle", style="filled", fillcolor=color_darker)
                        dot.edge(str(why.id), str(how.id), color="#999999", label=str(how.decompo_number),
                                 fontcolor="#999999")
                        plotted_edge.add((why.id, how.id))
                    how = why
                    why = why.why

            if action.previous is not None:
                if (action.id, action.previous.id) not in plotted_edge:
                    plotted_edge.add((action.id, action.previous.id))
                    dot.edge(str(action.previous.id), str(action.id), color="#FF5555")
            action = action.previous

    dot.render("graph_gui_hatpehda", view=True)

cd_results = "domains_and_results/results/runs/"

def show_all(actions, controlable_agent, uncontrolable_agent, n, with_contrib, with_delay, supports=[], threats=[], with_abstract="false", with_begin="false", causal_links="without", constraint_causal_edges="true", render_name="graph_gui_hatpehda", view=True):
    # with_abstract : "true"/"false"
    # with_begin : "true"/"false"
    # causal_links : "with"/"without"/"only"
    # constraint_causal_edges : "true"/"false"

    # Kill other graphs and remove previous files
    # os.system("pkill -f 'gthumb'")
    # os.system("find .. -name \"graph_gui_hatpehda*\" -exec rm {} \;")

    dot = Digraph(comment='Plan', format="png")
    dot.attr(fontsize="20") # nodesep, ranksep
    plotted_edge = set()


    if causal_links != "without" and causal_links != "with" and causal_links != "only":
        causal_link = "with"
    if causal_links == "only":
        constraint_causal_edges = "true"
        with_abstract = "false"

    for action in actions:
        while action is not None:
            if action.name == "BEGIN" and not with_begin=="true":
                action = None
                continue
            if action.name == "IDLE" and causal_links == "only":
                action = action.previous
                continue
            color = "#AAAAFF" if action.agent == controlable_agent else "#FFFFAA"
            color_darker = "#5555CC" if action.agent == controlable_agent else "#CCCC55"
            color_trig = "#5b5b96" if action.agent == controlable_agent else "#a3a462"
            parameters = action.parameters
            if action.name == "IDLE":
                shape = "octagon"
            elif action.name == "COM_ALIGN":
                shape = "doubleoctagon"
            else:
                shape = "ellipse"
            node_name = "BEGIN" if action.name == "BEGIN" else str(action.id)
            dot.node(str(node_name), str(action.id) + "-" + action.name + "\n(" + ",".join(map(lambda x: str(x), action.parameters)) + ")\n{} {}".format(action.current_plan_cost, action.cost), style="filled", fillcolor=color, shape=shape)
            why = action.why
            how = action
            if with_abstract == "true":
                while why is not None:
                    # If it is a trigger
                    if isinstance(why, str):
                        dot.node(why, why, shape="hexagon", style="filled", fillcolor=color_trig)
                        if (why, how.id) not in plotted_edge:
                            dot.edge(why, str(how.id), color="#04b808")
                            plotted_edge.add((why, how.id))
                        why=None
                    else:
                        if (why.id, how.id) not in plotted_edge:
                            if causal_links != "only":
                                dot.node(str(why.id), why.name + "\n(" + ",".join(map(lambda x: str(x), why.parameters)) + ")", shape="rectangle", style="filled", fillcolor=color_darker)
                                if with_begin=="true" or (why.name != "BEGIN" and how.name != "BEGIN"):
                                    edge_from = "BEGIN" if why.name == "BEGIN" else str(why.id)
                                    edge_to = "BEGIN" if how.name == "BEGIN" else str(how.id)
                                    dot.edge(edge_from, edge_to, color="#999999", label=str(how.decompo_number), fontcolor="#999999")
                                    plotted_edge.add((why.id, how.id))
                        how = why
                        why = why.why

            if action.previous is not None:
                if (action.id, action.previous.id) not in plotted_edge:
                    if causal_links != "only":
                        if with_begin=="true" or (action.previous.name != "BEGIN" and action.name != "BEGIN"):
                            edge_from = "BEGIN" if action.previous.name == "BEGIN" else str(action.previous.id)
                            edge_to = "BEGIN" if action.name == "BEGIN" else str(action.id)
                            plotted_edge.add((action.id, action.previous.id))
                            dot.edge(edge_from, edge_to, color="#000000")
            action = action.previous

    if causal_links != "without":
        for sup in supports:
            if with_begin=="true" or (sup.step.action.name != "BEGIN" and sup.target.action.name!= "BEGIN"):
                edge_from = "BEGIN" if sup.step.action.name == "BEGIN" else str(sup.step.action.id)
                edge_to = "BEGIN" if sup.target.action.name == "BEGIN" else str(sup.target.action.id)
                dot.edge(edge_from, edge_to, color="#32de10", label=str("sup"), constraint=constraint_causal_edges)
        for threat in threats:
            dot.edge(str(threat.target.action.id), str(threat.step.action.id), color="#ff0000", label=str("threat"), dir='back', constraint=constraint_causal_edges)

    str_contrib = "with_c" if with_contrib else "without_c"
    str_delay = "_with_d" if with_delay else ""
    render_name = "{}-{}{}".format(n, str_contrib, str_delay)
    dot.render(cd_results+render_name, view=view)
    os.system("rm {}{}".format(cd_results, render_name))


def show_tree(first_node, render_name="nodes_gui", view=True):
    dot = Digraph(comment='Nodes', format="png")
    dot.attr(fontsize="50", nodesep="0.5", ranksep="0.7")

    # shape = "plaintext"
    shape = "ellipse"
    node_height = "1.4"
    node_width = "2.0"

    to_refine = [first_node]
    make_dot_node(first_node, dot, shape, node_height, node_width)
    while to_refine!=[]:
        node = to_refine[0]
        to_refine.remove(node)
        for next in node.next_nodes:
            make_dot_node(next, dot, shape, node_height, node_width)
            dot.edge(str(node.id), str(next.id), label="   ", headlabel=next.start_action.branching_name, labeldistance="4.0", fontsize="20")
            to_refine.append(next)

    dot.render(cd_results+render_name, view=view)
    os.system("rm {}{}".format(cd_results, render_name))

def make_dot_node(node, dot, shape, node_height, node_width):
    selected_next=""
    if node.type == hatpehda.hatpehda.Node.Type.R:
        selected_next = "#" + str(node.selected_next)
    label = "{}#{}\n{} {} {}\n{}".format(nodeTypeStr(node.type), node.id, int(node.cost), nodeFlagStr(node.flag), node.fcost, selected_next)
    dot.node(str(node.id), label, style="filled", fillcolor=get_color(node), shape=shape, fixedsize="true", height=node_height, width=node_width, fontsize="25")

def nodeTypeStr(node_type):
    if node_type == hatpehda.hatpehda.Node.Type.F:
        type_str = "F"
    elif node_type == hatpehda.hatpehda.Node.Type.H:
        type_str = "H"
    elif node_type == hatpehda.hatpehda.Node.Type.I:
        type_str = "I"
    elif node_type == hatpehda.hatpehda.Node.Type.R:
        type_str = "R"
    return type_str

def nodeFlagStr(node_flag):
    if node_flag == hatpehda.hatpehda.Node.Flag.D:
        flag_str = "D"
    elif node_flag == hatpehda.hatpehda.Node.Flag.E:
        flag_str = "E"
    elif node_flag == hatpehda.hatpehda.Node.Flag.F:
        flag_str = "F"
    elif node_flag == hatpehda.hatpehda.Node.Flag.S:
        flag_str = "S"
    elif node_flag == hatpehda.hatpehda.Node.Flag.U:
        flag_str = "U"
    return flag_str

def get_color(node):
    if node.type == hatpehda.hatpehda.Node.Type.R:
        return "#A4C7FF"
    elif node.type == hatpehda.hatpehda.Node.Type.H:
        return "#FFDB9B"
    elif node.type == hatpehda.hatpehda.Node.Type.I:
        if node.flag == hatpehda.hatpehda.Node.Flag.E:
            return "#14F669"
        elif node.flag == hatpehda.hatpehda.Node.Flag.U:
            return "#1aa64f"
    elif node.flag == hatpehda.hatpehda.Node.Flag.S:
        return "#d24d4d"
    elif node.type == hatpehda.hatpehda.Node.Type.D:
        return "#ff7e00"
