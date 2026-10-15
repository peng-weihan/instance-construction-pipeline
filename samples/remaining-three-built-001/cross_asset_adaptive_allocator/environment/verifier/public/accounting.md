The trusted ledger, not the candidate's reported NAV, determines score.
At each t, candidate sees history through t-1, drifted pretrade weights and current NAV. If no rebalance, use drifted weights; do not silently restore yesterday's target.
Trading cost fraction = 0.0005*sum(abs(target-pretrade)); borrow fraction=0.03/252*sum(max(-w,0)); financing=0.05/252*max(-cash_weight,0).
Let net capital after these costs be NAV_net. New risky and cash amounts are NAV_net*w and NAV_net*cash_weight. Apply observed close-to-close returns; cash has zero return.
New NAV equals cash + sum(marked risky holdings); derive next drifted weights from those holdings. Fees must never be charged twice.
Weight constraints apply after cost normalization. Insufficient history must produce feasible conservative allocations, not missing days.
Policy must emit forecasts before the next return. VaR is a 5% return quantile (normally negative); a breach means realized return < forecast quantile.
Cold start and data gaps are explicit cases. No forward filling using future rows and no date-to-weight lookup. Execution is offline.
