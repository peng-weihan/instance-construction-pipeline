"""Implement initialize(metadata) and decide(history, state).
history includes prices only through previous close; state contains drifted weights,
cash, NAV and past execution/forecast records supplied by the trusted simulator.
Return all asset weights, risk_scale, variance_daily, q05_daily and rebalance_reason.
All returned numbers must be finite; submitted forecasts are stored before outcomes.
"""
def initialize(metadata): return {}
def decide(history, state):
    raise NotImplementedError('Implement risk model, constrained allocator and rebalance policy')
