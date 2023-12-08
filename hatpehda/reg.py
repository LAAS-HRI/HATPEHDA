import time

import rospy

from ontologenius import OntologiesManipulator, OntologyManipulator
from knowledge_sharing_planner_msgs.srv import Disambiguation, DisambiguationRequest
from knowledge_sharing_planner_msgs.msg import Triplet, SymbolTable

class REGHandler:
    def __init__(self):
        self.planning_ontologies_commit = {}
        self.ontos = OntologiesManipulator()
        self.ontos.waitInit()
        print("RegHandler Ready!")

    def cleanup(self):
        for agent in self.planning_ontologies_commit:
            rospy.loginfo("Deleting " + agent + "_planning")

            self.ontos.delete(agent+"_planning")
        self.planning_ontologies_commit = {}

    def get_re(self, agent_name, state, context, symbols, target):
        self.update_world(agent_name, state)
        disambiguation_req = DisambiguationRequest()
        disambiguation_req.individual = target
        disambiguation_req.ontology = agent_name + "_planning"
        disambiguation_req.baseFacts = [Triplet(s, p, o) for s, p, o in context]
        disambiguation_req.symbol_table = SymbolTable()
        for s, i in symbols.items():
            disambiguation_req.symbol_table.symbols.append(s)
            disambiguation_req.symbol_table.individuals.append(i)
        disambiguation_req.replan = False
        #print(disambiguation_req.baseFacts)
        disambiguate_srv = rospy.ServiceProxy('/KSP/disambiguate', Disambiguation)
        resp1 = disambiguate_srv(disambiguation_req)
        # print(disambiguation_req)
        # print("---")
        # print(resp1)
        #self.export_log(agent_name+"_planning")
        return resp1

    def get_res(self, agent_name, state, context, targets):
        self.update_world(agent_name, state)

    def update_world(self, agent_name, state):
        onto = self.get_planning_ontology(agent_name, state)
        onto.feeder.waitConnected()
        for type, entities in state.individuals.items():
            for e in entities:
                for rel in state.types[type]:
                    for on in getattr(state, rel)[e]:
                        #print("Adding relation", e, rel, on)
                        onto.feeder.addObjectProperty(e, rel, on)
        commit = onto.feeder.commitAuto()
        rospy.loginfo("Committed to ontology of agent " + agent_name)

    def get_planning_ontology(self, agent_name, state):
        if agent_name not in self.planning_ontologies_commit:
            self.create_planning_ontology(agent_name, state)
        onto = self.ontos.get(agent_name + "_planning")
        onto.feeder.checkout(self.planning_ontologies_commit[agent_name])
        return onto



    def create_planning_ontology(self, agent_name, state):
        planning_name = agent_name + "_planning"
        self.ontos.copy(planning_name, agent_name)
        planning_onto = self.ontos.get(planning_name)
        if planning_onto is None:
            print("""Could not create planning ontology with name '{dst}' by making a copy of '{src}'.
                  Ensure that that ontology '{src}' exists and '{dst}' does not.""".format(dst=planning_name, src=agent_name))
            return
        rospy.loginfo("Copied " + agent_name + " in " + planning_name)
        planning_onto.close()
        rospy.loginfo(planning_name + " closed")
        planning_onto.feeder.waitConnected()
        rospy.loginfo(planning_name + " connected")
        for type, entities in state.individuals.items():
            for e in entities:
                for rel in state.types[type]:
                    planning_onto.feeder.removeProperty(e, rel)
        self.planning_ontologies_commit[agent_name] = planning_onto.feeder.commitAuto()
        print("Created planning ontology (commit)", planning_name)

    def export_log(self, onto_name):
        self.ontos.get(onto_name).actions.export('/home/gbuisan/plop.xml')


