import hatpehda

"""
Simple travel domain to implement cost based algorithm.
Result:
with pruning:
Plan : [('walk', 'home', 'work')] with cost: 0.2


without pruning:
Plan : [('walk', 'home', 'work')] with cost: 0.2
Plan : [('go_to_parking',), ('drive', 'home', 'work'), ('come_from_parking',)] with cost: 0.3666666666666667

"""

def cost_travel_foot(dists, x, y):
    return dists[x][y] / 5.

def cost_travel_car(dists, x, y):
    return dists[x][y] / 60.

def cost_find_parking():
    return 0.25

def cost_get_back_from_parking():
    return 0.1

def walk(agents, self_state, agent_name, x, y):
    if self_state.loc[agent_name] == x:
        for a in agents.values():
            a.state.loc[agent_name] = y
        return agents, cost_travel_foot(self_state.dist, x ,y)
    else:
        return False, 0


def drive(agents, self_state, agent_name, x, y):
    if self_state.loc['car'] == x and self_state.loc[agent_name] == x and self_state.is_at_parking[agent_name] == True:
        for a in agents.values():
            a.state.loc['car'] = y
            a.state.loc[agent_name] = y
        return agents, cost_travel_car(self_state.dist, x, y)
    else:
        return False, 0


def go_to_parking(agents, self_state, agent_name):
    for a in agents.values():
        a.state.is_at_parking[agent_name] = True
    return agents, cost_find_parking()


def come_from_parking(agents, self_state, agent_name):
    for a in agents.values():
        a.state.is_at_parking[agent_name] = False
    return agents, cost_get_back_from_parking()


hatpehda.declare_operators("robot", walk, drive, go_to_parking, come_from_parking)
print('')
hatpehda.print_operators()


def travel_by_foot(agents, self_state, agent_name, x, y):
    return [('walk',x,y)]


def travel_by_car(agents, self_state, agent_name, x, y):
    return [('go_to_parking', ), ("drive", x, y), ("come_from_parking", )]

hatpehda.declare_methods("robot", "travel", travel_by_foot, travel_by_car)
hatpehda.print_methods()

state1_h = hatpehda.State("state1_h")
state1_h.places = ["home", "park", "work", "beach"]
state1_h.loc = {"robot": "home", "car": "home"}
state1_h.is_at_parking = {"human": False}
state1_h.dist = {"home": {"work": 1, "park": 0.5, "beach": 50}, "work": {"home": 1, "park": 1.5, "beach": 50},
                 "park": {"home": 0.5, "work": 1.5, "beach": 51}, "beach": {"home": 50, "work": 50, "park": 51}}

hatpehda.set_state("robot", state1_h)
hatpehda.add_tasks("robot", [('travel', "home", "work")])
# plans = hatpehda.multi_agent_planning()
# print(len(hatpehda.ma_solutions), " plans found !")
# for ags in hatpehda.ma_solutions:
#     print("Plan :", ags["robot"].global_plan, "with cost:", ags["robot"].global_plan_cost)

sol = []
plans = hatpehda.seek_plan_robot(hatpehda.agents, "robot", sol)

print(plans)

print(len(sol), "solutions found")
for agents in sol:
    for name, a in agents.items():
        print(name, "plan:", a.plan)
    print("######")
