import os

import pandas as pd

from DataScrape.ScrapeReddit import ASX_LISTING
from Datasets.scrape_data import replace_empties
from Services.Datafactory import DataFactory
from Services.MyLogger import MyLogger
from _config import TICKERS_LEDGER, ASX_GAME

if __name__ == "__main__":
    logger = MyLogger.getLogger("repair util", level=20)
    datafactory = DataFactory.getInstance()

    asx_game = pd.read_csv(ASX_GAME)

    to_replace = [s+".AX" for s in asx_game.Code]

    print(f"TO REPLACE ({len(to_replace)}):")
    for i, ticker in enumerate(to_replace):
        DFS = DataFactory.repaired
        try:
            print(f"{ticker} ({i + 1}/{len(to_replace)})")

            datafactory.repaired = False
            data = datafactory.loadSymbol(ticker).dropna()
            repaired_data = replace_empties(data)

            datafactory.repaired = True
            repaired_data.to_csv(datafactory.getDataDir("5 min") + datafactory.symbol2file(ticker))

        except Exception as e:
            logger.info("ERROR", f"Error replacing empties for ticker {ticker} - {e} ")
        finally:
            DataFactory.repairedDFS = DFS
