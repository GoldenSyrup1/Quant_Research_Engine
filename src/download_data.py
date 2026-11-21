import argparse
from pathlib import Path
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('--tickers', nargs='+', required=True)
parser.add_argument('--start', default='2015-01-01')
args = parser.parse_args()

for ticker in args.tickers:
    print(f"Downloading {ticker}")
    frame = yf.download(ticker, start=args.start, auto_adjust=True, progress=False)
    if frame.empty:
        print(f"No data returned for {ticker}")
        continue
    # auto_adjust=True adjusts OHLC for corporate actions; retain adjusted close-like Close.
    frame.to_csv(DATA / f"{ticker.replace('.', '_')}.csv")
print("Done. Check the files for missing dates and data quality before testing.")
