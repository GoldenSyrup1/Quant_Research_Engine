"""Utility functions for later extensions."""
import numpy as np

def max_drawdown(equity_curve):
    curve = np.asarray(equity_curve, dtype=float)
    peaks = np.maximum.accumulate(curve)
    return np.min(curve / peaks - 1.0)
