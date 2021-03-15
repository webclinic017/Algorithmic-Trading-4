import random

from Components.Account import Account
from Components.Process import ThreadedTask
from DataScrape.ScrapeReddit import ASX_LISTING
from Services.Datafactory import DataFactory
from Services.MyLogger import MyLogger
from Services.SimTracker import SimTracker
from Services.SimViewer import SimViewer

import pandas as pd

from Strategies.Breakouts import Breakouts
from Strategies.Crossover import Crossover
from Strategies.Crystal import CrystalV3
from Strategies.MACD import MACD
from Strategies.RocketCatcher import RocketCatcher
from Strategies.Testing import TestStrategy
from _config import TICKERS_LEDGER, ASX_GAME
import datetime

from enum import Enum

MyLogger.configure(level=20)

import matplotlib.pyplot as plt

plt.ioff()


if __name__ == "__main__":

    strategies = Enum('Strategy', 'Test Crystal RocketCatcher Breakouts MACD Crossover')
    strategy = strategies.Test


    DataFactory.repaired = True

    a = Account(5000)
    st = SimTracker()
    thread = None

    # Tickers on record
    tickers_ledger = pd.read_csv(TICKERS_LEDGER)
    tickers_ledger.index = pd.Index(tickers_ledger.TICKER)

    # Tickers on the ASX
    asx_listings = pd.read_csv(ASX_LISTING)
    asx_listings.index = pd.Index(asx_listings.code)

    # Tickers in the ASX game
    asx_game = pd.read_csv(ASX_GAME)
    asx_game.index = pd.Index(asx_game.Code)

    symbols = ["ASIA"]

    # symbols = random.choices(
    #     [s for s in asx_game.Code.values if asx_listings.loc[s].title.find("Ltd") > 0],
    #     k=15
    # )

    # symbols = random.choices(
    #     [s for t, s, mc, l in zip(
    #         asx_listings.title.values,
    #         asx_listings.code.values,
    #         asx_listings.market_cap.values,
    #         asx_listings.low.values)
    #      if
    #      (0.01 < l < 5) and
    #      (s + ".AX" in tickers_ledger.TICKER.values) and
    #      (t.find("Ltd") > 0)],
    #     k=100
    # )

    if strategy == strategy.Test:
        processargs = {
            "rapid": True,
            "times": [datetime.time(15, 30)],
            "setup_days": 50,
            "barsize": "1 day"
        }

        thread = ThreadedTask(st, a, [
            (TestStrategy, {
                "name": "SA",
                "symbols": symbols,
                "properties": {
                    "days_required": 250
                }})
        ], **processargs)

    elif strategy == strategy.Crystal:
        processargs = {
            "rapid": True,
            "setup_days": 30
        }

        thread = ThreadedTask(st, a, [
            (CrystalV3, {
                "name": "SA",
                "symbols": symbols,
                "properties": {
                    "days_required": 31,
                    "ma_days": 1,

                    "ma_long_days": 5,

                    "positive_sigma": 0.25,
                    "negative_sigma": 0.25,

                    "buy_volume_sigma": 2,
                    "sell_volume_sigma": 2
                }})
        ], **processargs)

    elif strategy == strategy.RocketCatcher:
        processargs = {
            "rapid": True
        }

        thread = ThreadedTask(st, a, [
            (RocketCatcher, {
                "name": "SA",
                "symbols": symbols,
                "properties": {
                    "days_required_5m": 3,
                    "days_required_1d": 31,
                    "from_max_limit": 20,
                    "from_min_limit": 15,
                    "volume_sigma": 0.25,
                    "pumps": 5
                }})
        ], **processargs)

    elif strategy == strategy.Breakouts:
        processargs = {
            "rapid": True,
            "times:": [datetime.time(15, 30)],
            "setup_days": 50
        }

        thread = ThreadedTask(st, a, [
            (Breakouts, {
                "name": "SA",
                "symbols": symbols,
                "properties": {
                    "days_required": 30
                }})
        ], **processargs)

    elif strategy == strategy.MACD:
        processargs = {
            "rapid": True,
        }

        thread = ThreadedTask(st, a, [
            (MACD, {
                "name": "SA",
                "symbols": symbols,
                "properties": {
                    "days_required_5m": 30,
                    "ema_short_days": 8,
                    "ema_long_days": 12,
                    "signal_line_days": 6
                }})
        ], **processargs)

    elif strategy == strategy.Crossover:
        processargs = {
            "rapid": True,
        }

        thread = ThreadedTask(st, a, [
            (Crossover, {
                "name": "SA",
                "symbols": symbols,
                "properties": {
                    "days_required": 30,
                    "sma_fast": 3,
                    "sma_med": 5,
                    "sma_slow": 9,

                }})
        ], **processargs)


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
