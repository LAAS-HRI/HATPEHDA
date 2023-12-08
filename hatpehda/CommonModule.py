class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

## Global variables and setters
g_robot_name=""
def set_robot_name(val):
    global g_robot_name
    g_robot_name = val
def get_robot_name():
    return g_robot_name
g_human_name=""
def set_human_name(val):
    global g_human_name
    g_human_name = val
def get_human_name():
    return g_human_name
g_other_agent_name={}
def init_other_agent_name():
    g_other_agent_name[g_robot_name] = g_human_name
    g_other_agent_name[g_human_name] = g_robot_name
    init_inactivity_costs()
g_wait_cost = {}
g_idle_cost = {}
g_delay_cost = {}
def init_inactivity_costs():
    g_wait_cost[g_robot_name]=0.0
    g_wait_cost[g_human_name]=2.0
    g_idle_cost[g_robot_name]=0.0
    g_idle_cost[g_human_name]=0.0
    g_delay_cost[g_robot_name]=0.0
g_starting_agent = g_robot_name
def set_starting_agent(agent):
    global g_starting_agent
    g_starting_agent = agent
g_debug = False
def set_debug(val):
    global g_debug
    g_debug = val
g_compute_gui = False
def set_compute_gui(val):
    global g_compute_gui
    g_compute_gui = val
g_view_gui = False
def set_view_gui(val):
    global g_view_gui
    g_view_gui = val
g_stop_input = False
def set_stop_input(val):
    global g_stop_input
    g_stop_input = val
g_debug_agenda = False
def set_debug_agenda(val):
    global g_debug_agenda
    g_debug_agenda = val
g_stop_input_agenda = False
def set_stop_input_agenda(val):
    global g_stop_input_agenda
    g_stop_input_agenda = val
g_with_contrib = True
def set_with_contrib(with_contrib):
    global g_with_contrib
    g_with_contrib = with_contrib
g_with_delay = False
def set_with_delay(with_delay):
    global g_with_delay
    g_with_delay = with_delay
