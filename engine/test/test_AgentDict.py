from engine.AgentDict import AgentDict

from enforce_typing import enforce_types

@enforce_types
def test1():
    class AgentBase:
        def __init__(self, name):
            self.name = name
    class FooAgent(AgentBase):
        pass
    class BarAgent(AgentBase):
        pass
    class BahAgent(AgentBase):
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

@enforce_types
def test_agentByAddress():
    class FooAgent:
        def __init__(self, name, address):
            self.name = name
            self.address = address

    d = AgentDict(
        {'foo1': FooAgent('foo1', 'address 111'),
         'foo2': FooAgent('foo2', 'address 222')
        })

    assert d.agentByAddress('address 111').address == 'address 111'
    assert d.agentByAddress('address 222').address == 'address 222'
    assert d.agentByAddress('address foo') is None
    
