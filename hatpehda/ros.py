import rospy
import json

from planner_msgs.msg import PlanRequest, Plan, AgentTasksRequest, Task

from .hatpehda import Goal

class RosNode:
    def __init__(self, name, on_new_request_cb):
        self.name = name
        self.user_callback = on_new_request_cb
        rospy.init_node(name)
        self.request_sub = rospy.Subscriber("~request_new_plan", PlanRequest, self.on_new_request)
        self.plan_pub = rospy.Publisher("~plan_answer", Plan, queue_size=10)
    @staticmethod
    def start_ros_node(node_name="planner", on_new_request=None):
        return RosNode(node_name, on_new_request)

    def retrieve_agents_task(self, agents_task_msg, agents_task):
        for ag in agents_task_msg:
            agents_task[ag.agent_name] = []
            for task in ag.tasks:
                arguments = []
                for ar in task.parameters:
                    try:
                        print("goal", ar)
                        j = json.loads(ar)
                        print(j)
                        goal = Goal("goal")
                        for p, indivs in j.items():
                            if not hasattr(goal, p):
                                goal.__setattr__(p, {})
                            for s, objs in indivs.items():
                                goal.__getattribute__(p)[s] = objs
                        arguments.append(goal)
                    except json.JSONDecodeError as e:
                        print(e)
                        arguments.append(ar) # We assume that if it is not JSON, it is a simple string
                agents_task[ag.agent_name].append((task.name, arguments))

    def on_new_request(self, msg: PlanRequest):
        ctrl_agents_task = {}
        unctrl_agents_task = {}
        self.retrieve_agents_task(msg.controllable_agent_tasks, ctrl_agents_task)
        self.retrieve_agents_task(msg.uncontrollable_agent_tasks, unctrl_agents_task)

        if self.user_callback is not None:
            self.user_callback(ctrl_agents_task, unctrl_agents_task)

    def wait_for_request(self):
        rospy.spin()

    def create_primitive_task(self, action):
        print(action)
        task = Task()
        task.id = action.id
        task.type = task.PRIMITIVE_TASK
        task.name = action.name
        task.parameters = [*action.parameters]
        task.agent = action.agent
        task.successors = []
        if action.why is None:
            task.decomposition_of = -1
        return task

    def send_plan(self, actions, ctrlable_name, unctrlable_name):
        existing_edges = set()
        existing_tasks = {}
        msg = Plan()
        msg.tasks = []
        for action in actions:
            while action is not None:
                if action.id not in existing_tasks:
                    task = self.create_primitive_task(action)
                    # print(task)
                    msg.tasks.append(task)
                    existing_tasks[action.id] = task
                task = existing_tasks[action.id]
                if action.previous is not None and action.previous.id not in task.predecessors:
                    task.predecessors.append(action.previous.id)
                if action.next is not None:
                    for n in action.next:
                        if n.id not in task.successors:
                            task.successors.append(n.id)
                why = action.why
                how = action
                while why is not None:
                    if (why.id, how.id) not in existing_edges:
                        if why.id not in existing_tasks:
                            print("adding", why.id, how.id)
                            task = Task()
                            task.id = why.id
                            task.type = task.ABSTRACT_TASK
                            task.name = why.name
                            task.parameters = []
                            for param in why.parameters:
                                #print("Parameter", param)
                                if isinstance(param, Goal):
                                    task.parameters.append("goal_{}".format(param.__name__))
                                else:
                                    task.parameters.append(param)
                            #print(task.parameters)
                            task.agent = why.agent
                            if why.why is None:
                                task.decomposition_of = -1
                            task.successors = []
                            existing_tasks[why.id] = task
                            msg.tasks.append(task)
                        why_task = existing_tasks[why.id]
                        how_task = existing_tasks[how.id]  # this one should exist
                        why_task.decomposed_into.append(how.id)
                        how_task.decomposition_of = why.id
                        how_task.decomposition_number = how.decompo_number
                        existing_edges.add((why.id, how.id))
                    how = why
                    why = why.why
                action = action.previous
        self.plan_pub.publish(msg)
