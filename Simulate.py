import random

from Components.Account import Account
from Components.Process import ThreadedTask
from DataScrape.ScrapeReddit import ASX_LISTING
from Services.Datafactory import DataFactory
from Services.MyLogger import MyLogger
from Services.SimTracker import SimTracker
from Services.SimViewer import SimViewer

import pandas as pd

from Strategies.Crystal import CrystalV3
from Strategies.MACD import MACD
from Strategies.RocketCatcher import RocketCatcher
from _config import TICKERS_LEDGER
import datetime

MyLogger.configure(level=MyLogger.TRADE)

import matplotlib.pyplot as plt

plt.ioff()

if __name__ == "__main__":
    # TODO: proper portfolio
    # TODO: data cleaning
    # TODO: parmas

    DataFactory.repaired = True

    a = Account(5000)
    st = SimTracker()

    tickers_ledger = pd.read_csv(TICKERS_LEDGER)
    asx_listings = pd.read_csv(ASX_LISTING)
    symbols = random.choices(
        [s for t, s, mc, l in zip(
            asx_listings.title.values,
            asx_listings.code.values,
            asx_listings.market_cap.values,
            asx_listings.low.values)
         if
         (0.01 < l < 5) and
         #(5 < l < 15) and
         (s + ".AX" in tickers_ledger.TICKER.values) and
         (t.find("Ltd") > 0)], k=100)

    #symbols += ["LGP", "PRL", "LKE", "LRS", "CPH"]
    #print(symbols)


    # days allowed - 15
    # from min

    # TODO: SETUP DAYS

    symbols = list(set(symbols))
    #symbols = ["FYI"]
    # thread = ThreadedTask(st, a,
    #                       [
    #                           (RocketCatcher, {
    #                               "name": "SA",
    #                               "symbols": symbols,
    #                               "properties": {
    #                                   "days_required_5m": 3,
    #                                   "days_required_1d": 31,
    #                                   "from_max_limit": 20,
    #                                   "from_min_limit": 15,
    #                                   "volume_sigma": 0.25,
    #                                   "pumps": 5
    #                               }})
    #                       ], rapid=True
    #                       )

    thread = ThreadedTask(st, a,
                          [
                              (RocketCatcher, {
                                  "name": "SA",
                                  "symbols": symbols,
                                  "properties": {
                                      "days_required_1d": 200 ,
                                      "from_max_limit": 20,
                                      "from_min_limit": 15,
                                      "volume_sigma": 0.25,
                                      "pumps": 5
                                  }})
                          ],
                          rapid=True,
                          barsize="1 day",
                          times=[datetime.time(15, 30)],
                          setup_days = 50
                          )


    # # thread = ThreadedTask(st, a,
    # #                       [
    # #                           (CrystalV3, {
    # #                               "name": "SA",
    # #                               "symbols": ["ASIA"],
    # #                               "properties": {
    # #                                   "days_required": 31,
    # #                                   "ma_days": 1,
    # #                                   "ma_long_days": 1,
    # #                                   "positive_sigma": 0.5,
    # #                                   "negative_sigma": 0.5,
    # #                                   "buy_volume_sigma": 2,
    # #                                   "sell_volume_sigma": 2
    # #                               }}),
    #                           # (CrystalV3, {
    #                           #     "name": "SA",
    #                           #     "symbols": ["BEAR"],
    #                           #     "properties": {
    #                           #         "days_required": 31,
    #                           #         "ma_days": 2,
    #                           #         "ma_long_days": 5,
    #                           #         "positive_sigma": 0.15,
    #                           #         "negative_sigma": 0.5
    #                           #     }}),
    #                       ]
    #                       )

    thread.start()
    root = SimViewer(st, a)
    thread.join()

"""
ADDITIONAL REQMARKETDATA CALLBACKS
tickPrice
tickSize
tickString
tickGeneric
tickEFP
deltaNeutralValidation
tickOptionComputation
tickSnapshotEnd
"""
