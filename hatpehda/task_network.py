from enum import Enum
from graphviz import Digraph
from hatpehda.hatpehda import Task

class Constraint:
    def __init__(self, start, end):
        self.start = start # id
        self.end = end # id
    
    def __repr__(self) -> str:
        return "{}>{}".format(self.start, self.end)

class TaskNetwork:
    def __init__(self):
        self.tasks = {} # {task_id:task}
        self.constraints = [] # [Constraints]
        self.first_tasks = [] # [Task]
        self.last_tasks = [] # [Task]

    def isEmpty(self):
        return len(self.task)==0

    def mergeTasks(self, tasks):
        new_tasks = {**self.tasks, **tasks}
        for key, value in new_tasks.items():
            if key in self.tasks and key in tasks:
                raise Exception("Same task in both TaskNetwok!")
        self.tasks = new_tasks

    def mergeConstraints(self, constraints):
        new_constraints = self.constraints + constraints
        for c in new_constraints:
            if c in self.constraints and c in constraints:
                raise Exception("Same constraint in both")
        self.constraints = new_constraints

    def hasConstraintFrom(self, task_id):
        for c in self.constraints:
            if task_id == c.start:
                return True
        return False

    def hasConstraintTo(self, task_id):
        for c in self.constraints:
            if task_id == c.end:
                return True
        return False

    def getConstraintsFrom(self, task_id):
        c_from = []
        for c in self.constraints:
            if task_id == c.start:
                c_from.append(c)
        return c_from

    def getConstraintsTo(self, task_id):
        c_to = []
        for c in self.constraints:
            if task_id == c.end:
                c_to.append(c)
        return c_to

    def computeFirstTasks(self):
        self.first_tasks = []
        for t in self.tasks:
            if not self.hasConstraintTo(t):
                self.first_tasks.append(self.tasks[t])
    
    def getFirstTasks(self):
        self.computeFirstTasks()
        return self.first_tasks

    def computeLastTasks(self):
        self.last_tasks = []
        for t in self.tasks:
            if not self.hasConstraintFrom(t):
                self.last_tasks.append(self.tasks[t])

    def getLastTasks(self):
        self.computeLastTasks()
        return self.last_tasks

    def replaceTaskByTN(self, task, tn):
        self.tasks.pop(task.id)
        self.mergeTasks(tn.tasks)
        self.constraints += tn.constraints
        # update constraints to 'task': t -> tn.first_tasks
        for ct in self.getConstraintsTo(task.id):
            self.constraints.remove(ct)
            for ft in tn.getFirstTasks():
                self.constraints.append( Constraint(ct.start, ft.id) )
        # update constraints from 'task': tn.last_tasks -> t
        for cf in self.getConstraintsFrom(task.id):
            self.constraints.remove(cf)
            for lt in tn.getLastTasks():
                self.constraints.append( Constraint(lt.id, cf.end) )

    def removeTask(self, task):
        self.tasks.pop(task.id)
        for cf in self.getConstraintsFrom(task.id):
            self.constraints.remove(cf)
        for ct in self.getConstraintsTo(task.id):
            self.constraints.remove(ct)

class TaskNetworkSingle(TaskNetwork):
    def __init__(self, task_name, *params):
        super().__init__()
        task = Task(task_name, params, None, None, "UNKW")
        self.tasks[task.id] = task
        self.first_tasks = [task]
        self.last_tasks = [task]

class TaskNetworkUnOrdered(TaskNetwork):
    def __init__(self, *tns):
        super().__init__()
        for tn in tns:
            self.mergeTasks(tn.tasks)
            self.constraints += tn.constraints

class TaskNetworkOrdered(TaskNetwork):
    def __init__(self, *tns):
        super().__init__()
        # merge current tasks and constraints
        for tn in tns:
            self.mergeTasks(tn.tasks)
            self.constraints += tn.constraints
        # create new constraints between task networks
        for i in range(len(tns)-1):
            for last_task in tns[i].getLastTasks():
                for first_task in tns[i+1].getFirstTasks():
                    self.constraints.append( Constraint(last_task.id, first_task.id) )

def show_tn(tn):
    dot = Digraph(comment='tn', format="png")
    dot.attr(fontsize="20")

    # tasks
    for t in tn.tasks.values():
        dot.node(str(t.id), "{}-{}".format(t.id, t.name) + "\n(" + ",".join(map(lambda x: str(x), t.parameters)) + ")")

    # constraints
    for c in tn.constraints:
        dot.edge(str(c.start), str(c.end))

    dot.render("plotted_tn", view=True)