import os

import pandas as pd

from DataScrape.ScrapeReddit import ASX_LISTING
from Datasets.scrape_data import replace_empties
from _config import TICKERS_LEDGER

if __name__ == "__main__":
    assert False, "broken don't run"

    src_files = os.listdir(r"C:\Users\liamd\Documents\Project\AlgoTrading\Datasets\CSV")
    for file_name in src_files:
        full_file_name = os.path.join(r"C:\Users\liamd\Documents\Project\AlgoTrading\Datasets\CSV", file_name)

        data = pd.read_csv(full_file_name)

        rows, cols = data.shape
        if cols > 7:
            print(file_name)

    asx_listings = pd.read_csv(ASX_LISTING)
    tickers_ledger = pd.read_csv(TICKERS_LEDGER)

    tickers = [s for s, mc, l in zip(asx_listings.code.values, asx_listings.market_cap.values, asx_listings.low.values)
               if l < 5 and s + ".AX" in tickers_ledger.TICKER.values]

    # tickers = pd.read_csv(TICKERS_LEDGER).TICKER.values -- 45

    for i, ticker in enumerate(['VAS']):
        print(f"{i + 1}/{len(tickers)}")
        replace_empties(ticker)
        # missing_times = t_range[~t_range.isin(t_dataframe)]
    print("")
