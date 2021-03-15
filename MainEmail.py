import datetime
import sched
import smtplib
import time
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz

from Components.Account import Account
from Components.Manager import Manager
from DataScrape.ScrapeReddit import ASX_LISTING
from Services.Datafactory import DataFactory
from Services.MyLogger import MyLogger
from Services.SimTracker import SimTracker
from Services.SimViewer import StrategyView
from Services.TradingClock import TradingClock
from Strategies.Crystal import CrystalV3
from Strategies.RocketCatcher import RocketCatcher
from _config import TICKERS_LEDGER
from _devconfig import *

import random
import pandas as pd



if __name__ == "__main__":

    MyLogger.configure(20)
    logger = MyLogger.getLogger("MAIN")

    # services
    DataFactory.repaired = True
    DataFactory.live_data = True
    clock, datafactory = TradingClock.getInstance(), DataFactory.getInstance()


    # absolute times to check for an update
    times = [
        datetime.time(9, 30),
        datetime.time(10, 30),
        datetime.time(11, 30),
        datetime.time(12, 30),
        datetime.time(13, 30),
        datetime.time(14, 30),
        datetime.time(15, 30),
        datetime.time(16, 30)
    ]
    dates = [clock.mytz.localize(datetime.datetime.combine(datetime.date.today(), time)) for time in times]
    clock.sync_datetime = dates.pop(0)

    # Components
    account = Account(100000)
    simtracker = SimTracker()
    manager = Manager(account, simtracker)
    strategy = CrystalV3(manager, "C3", ["VAS"], {
        "days_required": 31,
        "ma_days": 1,
        "buy_volume_sigma": 0.5,
        "sell_volume_sigma": 0.5,
        "ma_long_days": 3,
        "positive_sigma": 0.35,
        "negative_sigma": 0.3
    })  # not optimised

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
         (s + ".AX" in tickers_ledger.TICKER.values) and
         (t.find("Ltd") > 0)], k=5)

    strategy_two = RocketCatcher(manager, "RC", symbols, {
            "days_required_5m": 3,
            "days_required_1d": 31,
            "from_max_limit": 20,
            "from_min_limit": 15,
            "volume_sigma": 0.25,
            "pumps": 5
        })

    # PREPROCESSING -
    # 1. Data scrape / validate

    s = sched.scheduler(time.time, time.sleep)

    def run_update():
        # do your stuff
        clock.sync_datetime = dates.pop(0)

        logger.info(f"Running update... {datetime.datetime.now()}")

        try:
            strategy.update()
        except Exception as e:
            logger.exception(e)

        try:
            strategy_two.update()
        except Exception as e:
            logger.exception(e)

        if len(simtracker.snapshots):
            generate_message(simtracker, account)

        if not len(dates):
            return

        next = dates[0].astimezone(pytz.timezone('Australia/Brisbane'))
        s.enterabs(time.mktime(next.timetuple()), 1, run_update)
        # s.enter(1, 1, run_update)


    next = dates[0].astimezone(pytz.timezone('Australia/Brisbane'))
    s.enterabs(time.mktime(next.timetuple()), 1, run_update)
    # s.enter(1, 1, run_update)
    s.run()
