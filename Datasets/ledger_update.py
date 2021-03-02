import os

import pandas as pd

from DataScrape.ScrapeReddit import CSV_BASE, ASX_LISTING
from _config import TICKERS_LEDGER

if __name__ == "__main__":
    '''Add to the tickers ledger'''
    listings = pd.read_csv(ASX_LISTING)
    tickers_ledger = pd.read_csv(TICKERS_LEDGER)

    count = 0

    src_files = os.listdir(CSV_BASE)
    for file_name in src_files:
        full_file_name = os.path.join(CSV_BASE, file_name)
        symbol_sentiment = pd.read_csv(full_file_name)

        if sum(symbol_sentiment.mentions) > 0:
            symbol = file_name[:-4]
            if symbol in listings.code.values:
                symbol_yh = symbol + ".AX"
                if symbol_yh not in tickers_ledger.TICKER.values:
                    # print(symbol)
                    count += 1

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
    tickers_ledger.to_csv(TICKERS_LEDGER, index=False)
