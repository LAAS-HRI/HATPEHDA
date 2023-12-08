import rospy
from planner_msgs.msg import PlanRequest, Plan, AgentTasksRequest, Task, TaskRequest
import time

def ask_tidy_one(pub):
    msg = PlanRequest()
    robot_request = AgentTasksRequest()
    robot_request.agent_name = "robot"
    robot_task = TaskRequest()
    robot_task.name = "tidy_one"
    robot_task.parameters = ['cube_GBCG', 'throw_box_pink', 'human']
    robot_request.tasks.append(robot_task)
    msg.controllable_agent_tasks.append(robot_request)
    human_request = AgentTasksRequest()
    human_request.agent_name = "human"
    msg.uncontrollable_agent_tasks.append(human_request)

    pub.publish(msg)

def test_dt(pub):
    msg = PlanRequest()
    robot_request = AgentTasksRequest()
    robot_request.agent_name = "robot"
    robot_task = TaskRequest()
    robot_task.name = "tidy_cubes"
    robot_task.parameters = ["""
        {"isInContainer": {"cube_BGTG": ["throw_box_green"], "cube_GBTG": ["throw_box_green"]}}
    """]
    robot_request.tasks.append(robot_task)
    msg.controllable_agent_tasks.append(robot_request)
    human_request = AgentTasksRequest()
    human_request.agent_name = "human_0"
    msg.uncontrollable_agent_tasks.append(human_request)

    pub.publish(msg)

def test_icra(pub):
    msg = PlanRequest()
    robot_request = AgentTasksRequest()
    robot_request.agent_name = "robot"
    robot_task = TaskRequest()
    robot_task.name = "stack"
    robot_request.tasks.append(robot_task)
    msg.controllable_agent_tasks.append(robot_request)
    human_request = AgentTasksRequest()
    human_request.agent_name = "human_0"
    msg.uncontrollable_agent_tasks.append(human_request)

    pub.publish(msg)

if __name__ == "__main__":
    rospy.init_node("test_request")
    pub = rospy.Publisher("/planner/request_new_plan", PlanRequest, queue_size=1)
    while pub.get_num_connections() == 0:
        rospy.sleep(rospy.Duration(0.1))
    test_icra(pub)
    time.sleep(2)
