"""
Netlist to simulate oceanV3
"""

USE_EVM = True
from .SimStrategy import SimStrategy
from .SimState import SimState
from .KPIs import KPIs, netlist_createLogData, netlist_plotInstructions
