from graphviz import Digraph
import os

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

def show_all(actions, controlable_agent, uncontrolable_agent, supports=[], threats=[], with_abstract="false", with_begin="false", causal_links="without", constraint_causal_edges="true"):
    # with_abstract : "true"/"false"
    # with_begin : "true"/"false"
    # causal_links : "with"/"without"/"only"
    # constraint_causal_edges : "true"/"false"

    # Kill other graphs and remove previous files
    os.system("pkill -f 'gthumb'")
    os.system("find .. -name \"graph_gui_hatpehda*\" -exec rm {} \;")

    dot = Digraph(comment='Plan', format="png")
    dot.attr(fontsize="20")
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
            shape = "octagon" if action.name == "IDLE" else "ellipse"
            node_name = "BEGIN" if action.name == "BEGIN" else str(action.id)
            dot.node(str(node_name), action.name + "\n(" + ",".join(map(lambda x: str(x), action.parameters)) + ")", style="filled", fillcolor=color, shape=shape)
            why = action.why
            how = action
            if with_abstract == "true":
                while why is not None:
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

    dot.render("graph_gui_hatpehda", view=True)
