from DataScrape.ScrapeReddit import ASX_LISTING
from Services.MyLogger import MyLogger
from Strategies.Crystal import CrystalV3
from Strategies.RocketCatcher import RocketCatcher
from _config import TICKERS_LEDGER

MyLogger.configure(level=MyLogger.TRADE)
from Components.Account import Account
from Services.Datafactory import DataFactory
from Components.Process import ThreadedTask

import pandas as pd
import random


if __name__ == "__main__":
    # TODO: proper portfolio
    # TODO: data cleaning
    # TODO: parmas

    DataFactory.repaired = True

    logger = MyLogger.getLogger("Optimiser", file="optimiser.log", level=MyLogger.OPTY)

    def get_random_symbols(k=25):
        tickers_ledger = pd.read_csv(TICKERS_LEDGER)
        asx_listings = pd.read_csv(ASX_LISTING)
        return random.choices(
            [s for t, s, mc, l in zip(
                asx_listings.title.values,
                asx_listings.code.values,
                asx_listings.market_cap.values,
                asx_listings.low.values)
             if
             (0.01 < l < 5) and
             (s + ".AX" in tickers_ledger.TICKER.values) and
             (t.find("Ltd") > 0)], k=k)


    strat=1

    st = None
    if strat == 1:
        logger.optimisation(f"Rocket Catcher")
        parameter_set = {
            "days_required_5m": [3] * 20,
            "days_required_1d": [31] * 20,
            "volume_sigma": [0.2,0.2,0.2,0.2,0.2, 0.25,0.25,0.25,0.25,0.25, 0.35,0.35,0.35,0.35,0.35, 0.5,0.5,0.5,0.5,0.5],
            "pumps": [3,4,5,7,10, 3,4,5,7,10, 3,4,5,7,10, 3,4,5,7,10]
        }

        set_length = min([len(pp) for pp in parameter_set.values()])
        for i in range(set_length):
            properties = {
                k: v[i] for k, v in parameter_set.items()
            }

            DataFactory.clear()
            a = Account(1000000)
            thread = ThreadedTask(st, a,
                                  [
                                      (RocketCatcher, {
                                          "name": "SA",
                                          "symbols": get_random_symbols(35),
                                          "properties": properties
                                      })
                                  ], rapid=True
                                  )

            thread.start()
            thread.join()

            w,l = a.winRatio()
            ww,ll = a.winRatioNet()
            logger.optimisation(f"{properties}, {a.value}  {w} winners & {l} losers ({ww} winners and {ll} losers overall)")


    if strat == 3:
        for symbol in ["VAS"]:  # , "NDQ", "ASIA", "BEAR"]:
            set_length = 1

            # parameter_set = {
            #     "days_required": [31] * set_length,
            #     "sma_fast": [1, 1, 2, 3, 4, 5],
            #     "sma_med": [2, 2, 4, 6, 8, 10],
            #     "sma_slow": [3, 4, 8, 12, 16, 20]
            # }



            parameter_set = {
                "days_required": [31, 15, 10, 5, 31, 31, 31, 31, 31, 31],
                "ma_days": [1, 1, 1, 1, 2, 2, 2, 3, 3, 1],
                "ma_long_days": [3, 3, 3, 3, 4, 4, 5, 5, 6, 3],
                "positive_sigma": [0.2, 0.2, 0.2, 0.2, 0.1, 0.2, 0.3, 0.4, 0.5, 0.1],
                "negative_sigma": [0.2, 0.2, 0.2, 0.2, 0.05, 0.1, 0.015, 0.2, 0.25, 0.05]
            }
            # 4, 8, 16

            for i in range(set_length):
                properties = {
                    k: v[i] for k, v in parameter_set.items()
                }

                a = Account(10000)
                thread = ThreadedTask(st, a,
                                      [
                                          (CrystalV3, {
                                              "name": "SA",
                                              "symbols": ["VAS"],
                                              "properties": properties
                                          })
                                      ]
                                      )

                thread.start()
                thread.join()

                logger.optimisation(f"{properties}, {a.value}")
