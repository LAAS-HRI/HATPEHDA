# import simplexml
# sol={   'step': {'id':1, 'HA_id':1, 'HA':"pick", 'RA_id':2, 'RA':"place", 'best_rank':-1, 'children':{
#                 'step': {'id',2,
#                 },
#                 'step': {'id',3,
#                 },
#                 },
#             }
#         }

# f = open("test.xml", 'w')
# f.write(simplexml.dumps(sol))
# f.close()
import sys
sys.path.insert(0, "/home/afavier/ws/HATPEHDA/domains_and_results/")
import ConcurrentModule as ConM
import CommonModule as CM

LOAD =  False
WRITE = False

import simplexml

LOAD = True
# WRITE = True

if WRITE:
    data = {'person':{'name':'joaquim','age':15,'cars':[{'id':1},{'id':2}]}}


    data={   'step': [
            {'id':1, 'HA_id':1, 'HA':"pick", 'RA_id':2, 'RA':"place", 'best_rank':-1, 'step':[
                {'id':2, 'step':[
                    {'id':4},
                ]},
                {'id':3, 'step':[
                    {'id':5, 'step':[
                        {'id':6},
                    ]},
                ]},
            ]},
        ]}
    
    f = open("test.xml", 'w')
    f.write(simplexml.dumps(data))
    f.close()

elif LOAD:
    f = open("test.xml", 'r')
    f.readline()
    content = f.read()
    print("\nFrom file:\n", content)

    content = content.replace(' ', '')
    content = content.replace('\t', '')
    content = content.replace('\n', '')
    head = '<?xml version="1.0"?>'
    content = head + content
    print("\nTreated:\n", content)

    data = simplexml.loads(content)
    f.close()
    print("\nloaded:\n", data)

    # Step :        <id>, [<pair>]
    # Pair :        <HA_id>, <HA>, <RA_id>, <RA>, <best_reachable_rank>, <step>
    # Final Pair :  <HA_id>, <HA>, <RA_id>, <RA>, <best_reachable_rank>, <branch_metrics>

    def get_name_and_parameters(full_action_name):
        if full_action_name[:len("PASSIVE")] == "PASSIVE":
            name = "PASSIVE"
            raw_params = full_action_name[len("PASSIVE")+1:-1].split(",")
            parameters = []
            for para in raw_params:
                parameters.append(para.replace("'", ""))
        else:
            i_find = full_action_name.find('(')
            name = full_action_name[:i_find]
            raw_params = full_action_name[i_find+1:-1].split(",")
            parameters = []
            for para in raw_params:
                parameters.append(para.replace("'", ""))
        return name, parameters

    def convert_step_dict_to_Step(dict_step, from_step, from_pair):

        step = ConM.Step(parent=from_step)

        if isinstance(dict_step['pair'], list):
            dict_pairs = dict_step['pair']
        else:
            dict_pairs = [dict_step['pair']]
        final_step = len(dict_pairs)==1 and 'metrics' in dict_pairs[0]
        action_pairs = []
        for p in dict_pairs:
            r_name, r_parameters = get_name_and_parameters(p["RA"])
            RA = CM.Action()
            RA.minimal_init(p["RA_id"], r_name, r_parameters, "R")

            h_name, h_parameters = get_name_and_parameters(p["HA"])
            HA = CM.Action()
            HA.minimal_init(p["HA_id"], h_name, h_parameters, "H")

            action_pair = ConM.ActionPair(HA, RA, None)
            action_pairs.append(action_pair)

            if final_step:
                # read metrics
                action_pair.branch_metrics = p['metrics']
            elif not final_step:
                # keep exploring
                convert_step_dict_to_Step(p["step"], step, action_pair)

        human_options = ConM.arrange_pairs_in_HumanOption(action_pairs)
        step.init(human_options, from_pair)
        step.id = dict_step['id']

        return step
    
    domain_name = data['sol']['domain_name']
    initial_state = data['sol']['initial_state']
    begin_step = convert_step_dict_to_Step(data['sol']['begin_step'], None, None)
    print("oihoi")

