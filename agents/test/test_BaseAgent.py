import enforce
import pytest

from agents.BaseAgent import *

@enforce.runtime_validation
class MyTestAgent(BaseAgent):
    def takeStep(self, state):
        pass

@enforce.runtime_validation
def testInit():
    agent = MyTestAgent("agent1", USD=1.1, OCEAN=1.2)
    assert agent.name == "agent1"
    assert agent.USD() == 1.1
    assert agent.OCEAN() == 1.2
    assert "MyTestAgent" in str(agent)

@enforce.runtime_validation
def testReceiveAndSend():
    #agents are of arbitary classes
    agent = MyTestAgent("agent1", USD=0.0, OCEAN=3.30)
    agent2 = MyTestAgent("agent2", USD=0.0, OCEAN=3.30)

    #USD
    assert pytest.approx(agent.USD()) == 0.00
    agent.receiveUSD(13.25)
    assert pytest.approx(agent.USD()) == 13.25

    agent._transferUSD(None, 1.10)
    assert pytest.approx(agent.USD()) == 12.15

    assert pytest.approx(agent2.USD()) == 0.00
    agent._transferUSD(agent2, 1.00)
    assert pytest.approx(agent.USD()) == (12.15 - 1.00)
    assert pytest.approx(agent2.USD()) == (0.00 + 1.00)

    #OCEAN
    assert pytest.approx(agent.OCEAN()) == 3.30
    agent.receiveOCEAN(2.01)
    assert pytest.approx(agent.OCEAN()) == 5.31

    agent._transferOCEAN(None, 0.20)
    assert pytest.approx(agent.OCEAN()) == 5.11

    assert pytest.approx(agent2.OCEAN()) == 3.30
    agent._transferOCEAN(agent2, 0.10)
    assert pytest.approx(agent.OCEAN()) == (5.11 - 0.10)
    assert pytest.approx(agent2.OCEAN()) == (3.30 + 0.10)
