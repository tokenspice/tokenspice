from agents.AgentDict import AgentDict

from enforce_typing import enforce_types # type: ignore[import]

@enforce_types
def test1():
    class BaseAgent:
        def __init__(self, name):
            self.name = name
    class FooAgent(BaseAgent):
        pass
    class BarAgent(BaseAgent):
        pass
    class BahAgent(BaseAgent):
        pass
    
    d = AgentDict({'foo1': FooAgent('foo1'),
                   'foo2': FooAgent('foo2'),
                   'bar1': BarAgent('bar1')})

    foo_d = d.filterByClass(FooAgent)
    assert sorted(foo_d.keys()) == ['foo1', 'foo2']
    
    bar_d = d.filterByClass(BarAgent)
    assert sorted(bar_d.keys()) == ['bar1']
    
    bah_d = d.filterByClass(BahAgent)
    assert sorted(bah_d.keys()) == []

@enforce_types
def test2():
    class FooAgent:
        def __init__(self, name):
            self.name = name
        def BPT(self, pool):
            return 0.0
        
    d = AgentDict({'foo1': FooAgent('foo1')})
    assert not d.filterByNonzeroStake(FooAgent('foo2'))

    assert not d.filterToPool()
    
    assert not d.filterToPublisher()
    
    assert not d.filterToStakerspeculator()
    
    assert not d.filterToDataconsumer()
    
    assert len(d.filterByClass(FooAgent)) == 1
    
