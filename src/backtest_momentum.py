from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = ROOT / 'outputs'
OUT.mkdir(exist_ok=True)

LOOKBACK = 126
SKIP = 21
N_HOLD = 5
COST_BPS = 10  # simplistic cost per one-way portfolio turnover

files = sorted(DATA.glob('*.csv'))
if len(files) < N_HOLD:
    raise SystemExit(f"Need at least {N_HOLD} ticker files in {DATA}. Run download_data.py first.")

prices = {}
for f in files:
    try:
        df = pd.read_csv(f, index_col=0, header=[0,1], parse_dates=True)
        # yfinance multiindex CSV can differ across versions; extract Close robustly.
        if isinstance(df.columns, pd.MultiIndex):
            cols = df.columns.get_level_values(0)
            field = 'Close' if 'Close' in cols else cols[0]
            s = df[field].iloc[:, 0] if isinstance(df[field], pd.DataFrame) else df[field]
        else:
            df = pd.read_csv(f, index_col=0, parse_dates=True)
            s = df['Close']
        s = pd.to_numeric(s, errors='coerce')
        prices[f.stem.replace('_AX','').replace('_','.')]=s
    except Exception as e:
        print(f"Skipping {f.name}: {e}")

px = pd.DataFrame(prices).sort_index().dropna(how='all')
px = px.ffill(limit=3)
ret = px.pct_change().fillna(0)
# Momentum signal excludes the most recent month to reduce short-term reversal effects.
signal = px.shift(SKIP) / px.shift(LOOKBACK + SKIP) - 1
rebalance_dates = signal.resample('ME').last().index
weights = pd.DataFrame(0.0, index=px.index, columns=px.columns)
current = pd.Series(0.0, index=px.columns)
for date in rebalance_dates:
    idx = signal.index[signal.index <= date]
    if len(idx) == 0: continue
    d = idx[-1]
    ranked = signal.loc[d].dropna().sort_values(ascending=False)
    selected = ranked.head(N_HOLD).index
    target = pd.Series(0.0, index=px.columns)
    if len(selected): target.loc[selected] = 1.0 / len(selected)
    # apply target beginning next trading day to reduce look-ahead
    future = px.index[px.index > d]
    if len(future): current = target
    weights.loc[d] = current
# Forward-fill portfolio weights, and shift one day so signal changes aren't applied on same close.
weights = weights.ffill().fillna(0).shift(1).fillna(0)
# Rebalance turnover calculated from daily changes in weights.
turnover = weights.diff().abs().sum(axis=1).fillna(0)
cost = turnover * (COST_BPS / 10000)
portfolio_ret = (weights * ret).sum(axis=1) - cost
curve = (1 + portfolio_ret).cumprod()
bench = (1 + ret.mean(axis=1)).cumprod()  # equal-weight universe proxy, NOT a market benchmark

metrics = {
    'strategy_total_return': float(curve.iloc[-1] - 1),
    'proxy_total_return': float(bench.iloc[-1] - 1),
    'strategy_ann_return': float(curve.iloc[-1] ** (252 / max(len(curve), 1)) - 1),
    'strategy_ann_vol': float(portfolio_ret.std() * np.sqrt(252)),
    'strategy_sharpe_approx': float((portfolio_ret.mean() / portfolio_ret.std()) * np.sqrt(252)) if portfolio_ret.std() else np.nan,
    'strategy_max_drawdown': float((curve / curve.cummax() - 1).min()),
    'total_turnover': float(turnover.sum()),
    'cost_assumption_bps': COST_BPS,
}
curve.rename('strategy').to_frame().join(bench.rename('equal_weight_universe_proxy')).to_csv(OUT / 'equity_curve.csv')
pd.Series(metrics).to_csv(OUT / 'metrics.csv', header=['value'])
portfolio_ret.rename('daily_return').to_csv(OUT / 'daily_returns.csv')
print(pd.Series(metrics).to_string())
print('\nWARNING: Exploratory backtest. Proxy benchmark and sample universe have limitations; no trade execution. Review README.')
