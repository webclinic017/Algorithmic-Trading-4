import functools
import threading

from Components.Manager import Manager
from Services.Datafactory import DataFactory
from Services.MyLogger import MyLogger
from Services.TradingCalendar import TradingCalendar
from Services.TradingClock import TradingClock

# UNIT TESTING?
# MIDDLEMAN TO SANITISE TRADING ?

# import logging

#MyLogger.configure()
import datetime
import matplotlib.pyplot as plt

plt.ioff()


class ThreadedTask(threading.Thread):
    def __init__(self, simtracker, account, strategies, rapid=False, times=None, setup_days=3, barsize="5 min"):
        threading.Thread.__init__(self)

        self.simtracker = simtracker
        self.account = account
        self.logger = MyLogger.getLogger('main')
        self.strategies = strategies
        self.symbols = functools.reduce(lambda a, b: set(a + b), [skwa["symbols"] for s, skwa in strategies])
        self.barsize = barsize
        self.rapid = rapid
        self.setup_days = setup_days

        if times is None:
            self.times = [
                datetime.time(10, 30),
                datetime.time(11, 30),
                datetime.time(12, 30),
                datetime.time(13, 30),
                datetime.time(14, 30),
                datetime.time(15, 30),
            ]
        else:
            self.times = times

    def run(self):
        DataFactory.prejack_symbols = self.symbols
        clock, datafactory = TradingClock.getInstance(), DataFactory.getInstance()

        # Configure
        # TODO: TOML

        # Where do we have available data
        earliest_data, latest_data = datafactory.datesSpread(barsize=self.barsize)
        start_date = TradingCalendar.add_trading_days(earliest_data, self.setup_days)
        end_date = latest_data  # TradingCalendar.add_trading_days(clock.date, 1)
        # clock.set_day(TradingCalendar.add_trading_days(latest_data, -12))

        # Get a groove on
        clock.set_day(start_date)
        while (clock.date <= end_date):
            self.logger.info(clock.date)

            # Daily setup
            m = Manager(self.account, self.simtracker)
            strategies = [stype(m, **strategy_kwargs) for stype, strategy_kwargs in self.strategies]

            # Guts of the simulation
            if self.rapid:
                for simtime in [clock.mytz.localize(datetime.datetime.combine(clock.date, time)) for time in self.times]:
                    clock.sync_datetime = simtime
                    for strategy in strategies:
                        strategy.update()

            else:
                for simtime in TradingCalendar.tradingtimes(clock.date):
                    clock.sync_datetime = simtime

                    # On the hour
                    # if clock.sync_datetime.time().hour > 10 and clock.sync_datetime.time().minute == 0:

                    if clock.sync_datetime.time() in self.times:
                        # todo: need to really use the tws api before figuring this out..
                        for strategy in strategies:
                            strategy.update()

            if clock.date == end_date:
                for strategy in strategies:
                    strategy.closeall()

            # Daily teardown
            m.stop()

            # NEXT!
            clock.roll_day()

        self.account.stop()

        print("THREAD DONE.")
