from collections import namedtuple

class REGHandler:
    MockREGAnswer = namedtuple("MockREGAnswer", ["success"])

    def __init__(self):
        print("WARNING: Running a mocked REG Handler.")

    def cleanup(self):
        print("WARNING: Running a mocked REG Handler (cleanup simulated).")

    def get_re(self, agent_name, state, context, symbols, target):
        print("WARNING: Running a mocked REG Handler (REG simulated).")
        return self.MockREGAnswer(success=True)
