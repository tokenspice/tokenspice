import logging
log = logging.getLogger('minteragents')

from enforce_typing import enforce_types # type: ignore[import]
import math

from agents.BaseAgent import BaseAgent    
from util.constants import S_PER_YEAR, BITCOIN_NUM_HALF_LIVES

#====================================================================
# Linear minting
"""
Mints OCEAN according to a schedule, then send to receiving agent.

Minting schedule is linear (flat): same # OCEAN tokens each time, n times.
"""

@enforce_types
class OCEANLinearMinterAgent(BaseAgent):
    def __init__(self, name: str, 
                 receiving_agent_name: str,
                 total_OCEAN_to_mint: float,
                 s_between_mints: int,  n_mints: int):
        assert total_OCEAN_to_mint >= 0.0
        if total_OCEAN_to_mint > 0.0:
            assert n_mints > 0
        
        super().__init__(name, USD=0.0, OCEAN=0.0)
        self._receiving_agent_name: str = receiving_agent_name
        self._s_between_mints: int = s_between_mints
        self._OCEAN_per_mint: float = total_OCEAN_to_mint / float(n_mints)
        
        self._tick_previous_mint = None
        self._n_mints_left: int = n_mints
        
    def takeStep(self, state):        
        if self._doMint(state):
            self._mintAndDisburseFunds(state)

    def _doMint(self, state) -> bool:
        assert self._n_mints_left >= 0.0
        
        if self._n_mints_left == 0:
            return False
        elif self._tick_previous_mint is None:
            return True
        else:
            n_ticks_since = state.tick - self._tick_previous_mint
            n_s_since = n_ticks_since * state.ss.time_step
            n_s_thr = self._s_between_mints            
            return (n_s_since >= n_s_thr)
        
    def _mintAndDisburseFunds(self, state):
        assert self._n_mints_left > 0, "only call if mints are left"

        OCEAN: float = self._OCEAN_per_mint #mint!
        
        state._total_OCEAN_minted += OCEAN
        self.receiveOCEAN(OCEAN)
        
        receiving_agent = state.getAgent(self._receiving_agent_name)
        self._transferOCEAN(receiving_agent, OCEAN)
        
        self._tick_previous_mint = state.tick
        self._n_mints_left -= 1

#====================================================================
# Minting funcs: Exponential, exponential with ratchet 

@enforce_types
class ExpFunc:
    """
    F(H,t) = 1 - (0.5*t/H). i.e. like Bitcoin.

    Where
    -t = time passed (years) (=4 for Bitcoin)
    -H = half life. By H=t, 50% of tokens are dispensed. By H=2t, 75%. Etc.
    """

    def __init__(self, H: float):
        assert H > 0.0
        self._H: float = H     

    def __call__(self, t: float) -> float:
        H = self._H
        return 1.0 - math.pow(0.5,t/H)

    def keepMinting(self, t:float) -> bool:
        num_half_lives = t / self._H
        return num_half_lives <= BITCOIN_NUM_HALF_LIVES
    
@enforce_types
class RampedExpFunc:
    """
    Bitcoin follows the following formula for supply of tokens
    F(H,t) = 1 - (0.5*t/H). 

    Where
    -t = time passed (years)
    -H = half life. By H=t, 50% of tokens are dispensed. By H=2t, 75%. Etc.

    So, minting is aggressive in the first 4 years. That's ok for Bitcoin.

    Challenges:
    -Minting aggressively in first few years + low liquidity --> downwards price pressure
    -Bumpy funding in first few years: lots from $ from BDB + OPF + minting, then drop when less from BDB + OPF. Better: avoid a dropoff, such that flat or increasing.
    -OceanDAO will take months or years to stabilize. Dangerous to give too much $ to OceanDAO when it's still unstable.

    To address these challenges:
    -We ratchet up the multiplier of rewards from small initially (10%), then 25% after interval 0 (eg 0.5 years), then 50% after another interval (eg 0.5 years), and finally 100% after a final interval (e.g. 1 year).

    We considered having ratchets based on milestones other than time. However, non time-based milestones add complexity and are harder to govern.

    = Equations =
    g(t) is the overall network rewards schedule. It’s a piecewise model of four exponential curves.

    g(t) = { 0      t < T0
           { g1(t)  T0 <= t < T1
           { g2(t)  T1 <= t < T2
           { g3(t)  T2 <= t < T3
           { g4(t)  otherwise

    Where gi(t) are pieces of the piecewise model chosen depending on t, and Gi are the values of gi(t) at the inflection points.

    G1=g1(t=T1); G2=g2(t=T2); G3=g3(t=T3)
    g1(t) = M1*f(t-T0)
    g2(t) = M2*f(t-T0) - M2*f(T1-T0) + G1
    g3(t) = M3*f(t-T0) - M3*f(T2-T0) + G2
    g4(t) = (1-G3)*f(t-T3) + G3

    And f(t) is the value of F(H,t) assuming a constant H. F(H,t) is the 
      base exponential curve. The units of H and t are years.
    f(t) = F(H,t)
    F(H,t) = 1 - (0.5*t/H). This is the Bitcoin formula (if H=4)

    The pieces of the model are a function of t, which are parameterized 
    with Ti. The units of Ti are years.

    Example parameter settings:
    H=4 years
    T0=0.0
    T1=0.5
    T2=1.0
    T3=2.0
    M1=0.10
    M2=0.25
    M3=0.50
    """

    def __init__(self, H, T0, T1, T2, T3, M1, M2, M3):
        assert H > 0.0
        assert T0 <= T1 <= T2 <= T3
        assert M1 <= M2 <= M3
        
        self._H = H        
        self._T0, self._T1, self._T2, self._T3 = T0, T1, T2, T3
        self._M1, self._M2, self._M3 = M1, M2, M3

    def __call__(self, t):
        return self._MYG(t)

    def keepMinting(self, t:float) -> bool:
        num_half_lives = t / self._H
        return num_half_lives <= BITCOIN_NUM_HALF_LIVES

    def _MYG(self, t):
        MYG1, MYG2, MYG3, MYG4 = self._MYG1, self._MYG2, self._MYG3, self._MYG4
        T0, T1, T2, T3 = self._T0, self._T1, self._T2, self._T3
        G1 = MYG1(t)
        G2 = MYG2(t,G1)
        G3 = MYG3(t,G1,G2)

        if (t < T0):
            return 0.0
        elif (t < T1):
            return MYG1(t)
        elif (t < T2):
            return MYG2(t, G1)
        elif (t < T3):
            return MYG3(t, G1, G2)
        else:
            return MYG4(t, G1, G2, G3)

    def _MYG1(self, t):
        MYF = self._MYF
        M1 = self._M1
        T0 = self._T0
        return M1 * MYF(t-T0)

    def _MYG2(self, t, G1):
        MYF = self._MYF
        M1, M2 = self._M1, self._M2
        T0, T1 = self._T0, self._T1
        return M2*MYF(t-T0) - M2*MYF(T1-T0) + G1

    def _MYG3(self, t, G1, G2):
        MYF = self._MYF
        M1, M2, M3 = self._M1, self._M2, self._M3
        T0, T1, T2 = self._T0, self._T1, self._T2
        return M3*MYF(t-T0) - M3*MYF(T2-T0) + G2

    def _MYG4(self, t, G1, G2, G3):
        MYF = self._MYF
        M4 = 1.0 - G3
        T3 = self._T3
        return M4*MYF(t-T3) + G3

    def _MYF(self, t):
        H = self._H
        return 1.0 - math.pow(0.5,t/H)
    
@enforce_types
class OCEANFuncMinterAgent(BaseAgent):
    def __init__(self, name: str, 
                 receiving_agent_name: str,
                 total_OCEAN_to_mint: float,
                 s_between_mints: int,
                 func,
    ):
        assert total_OCEAN_to_mint >= 0.0
        
        super().__init__(name, USD=0.0, OCEAN=0.0)
        self._receiving_agent_name: str = receiving_agent_name
        self._total_OCEAN_to_mint: float = total_OCEAN_to_mint
        self._s_between_mints: int = s_between_mints
        self._func = func #e.g. RampedExpFunc
        
        self._tick_previous_mint = None
        self._OCEAN_left_to_mint: float = total_OCEAN_to_mint
        
    def takeStep(self, state):        
        if self._doMint(state):
            self._mintAndDisburseFunds(state)

    def OCEANminted(self):
        return self._total_OCEAN_to_mint - self._OCEAN_left_to_mint

    def _doMint(self, state) -> bool:
        if self._OCEAN_left_to_mint == 0.0:
            return False
        elif state.tick == 0:
            return False
        elif self._tick_previous_mint is None:
            return True
        else:
            n_ticks_since = state.tick - self._tick_previous_mint
            n_s_since = n_ticks_since * state.ss.time_step
            n_s_thr = self._s_between_mints            
            return (n_s_since >= n_s_thr)

    def _mintAndDisburseFunds(self, state):
        assert self._OCEAN_left_to_mint > 0.0, "only call if mints are left"
        
        t = state.tick * state.ss.time_step / S_PER_YEAR
        G_t = self._func(t)

        if self._tick_previous_mint is None:
            tprev = 0.0
        else:
            tprev = self._tick_previous_mint * state.ss.time_step / float(S_PER_YEAR)
        G_tprev = self._func(tprev)
        
        percent_to_mint = G_t - G_tprev 

        #mint!
        OCEAN: float = percent_to_mint * self._total_OCEAN_to_mint

        if not self._func.keepMinting(t):
            OCEAN = self._OCEAN_left_to_mint
        OCEAN = min(OCEAN, self._OCEAN_left_to_mint) #don't mint > OCEAN left
        
        state._total_OCEAN_minted += OCEAN
        self.receiveOCEAN(OCEAN)
        
        receiving_agent = state.getAgent(self._receiving_agent_name)
        self._transferOCEAN(receiving_agent, OCEAN)
        
        self._tick_previous_mint = state.tick
        self._OCEAN_left_to_mint -= OCEAN
