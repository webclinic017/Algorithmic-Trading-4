import pandas as pd

from _config import TICKERS_LEDGER

if __name__ == "__main__":
    asx_game = pd.read_csv('companies_asxgame.csv')

    symbols = [c +'.AX' for c in asx_game.Code]


    tickers_ledger = pd.read_csv(TICKERS_LEDGER)

    tickers = tickers_ledger.TICKER


    tickers_ledger = pd.concat([
        tickers_ledger,
        pd.DataFrame({
            "TICKER": symbols,
            "CAT": [1] * len(symbols),
            "STATUS": [""]* len(symbols),
            "COLL_LAST": [""] * len(symbols),
            "COLL_FREQ": [1] * len(symbols),
            "REPAIR_LAST": [""] * len(symbols),
            "REPAIR_FREQ": [5] * len(symbols),
            "MISSING_DATES": [0] * len(symbols),
            "MISSING_TIMES": [0] * len(symbols)
        }, index=range(len(symbols)))])


    tickers_ledger.index = pd.Index(tickers_ledger.TICKER)

    tickers_ledger = tickers_ledger[~tickers_ledger.index.duplicated(keep='last')]

    tickers_ledger.to_csv(TICKERS_LEDGER, index=False)