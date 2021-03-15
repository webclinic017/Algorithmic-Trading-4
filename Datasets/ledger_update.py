import os

import pandas as pd

from DataScrape.ScrapeReddit import CSV_BASE, ASX_LISTING
from _config import TICKERS_LEDGER

if __name__ == "__main__":
    '''Add to the tickers ledger'''
    listings = pd.read_csv(ASX_LISTING)
    listings.index = pd.Index(listings.code)

    tickers_ledger = pd.read_csv(TICKERS_LEDGER)
    tickers_ledger.index = pd.Index(tickers_ledger.TICKER)

    counter = 0
    for i, row in listings.iterrows():
        symbol = row["code"]
        low = row["52w_low"]
        high = row["52w_high"]
        last = row["last"]

        change_52w = (high - low)/low if low > 0 else 0
        dreadful = last < 1
        allow = change_52w > 1 or dreadful
        if not allow:
            continue


        symbol_yh = symbol + ".AX"
        if symbol_yh not in tickers_ledger.TICKER.values:
            print(symbol_yh)
            counter += 1
            symbols_dict = {
                "TICKER": symbol_yh,
                "CAT": 99,
                "STATUS": "",
                "COLL_LAST": "",
                "COLL_FREQ": 55,
                "REPAIR_LAST": "",
                "REPAIR_FREQ": 55,
                "MISSING_DATES": 0,
                "MISSING_TIMES": 0,
            }
            tickers_ledger = tickers_ledger.append(symbols_dict, ignore_index=True)

    print(f"Adding {counter} tickers")
    tickers_ledger.to_csv(TICKERS_LEDGER, index=False)
