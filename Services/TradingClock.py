import datetime
import sys

import pytz
from dateutil import tz

sys.path.append('..')
from Services.TradingCalendar import TradingCalendar


class TradingClock:
    __instance = None

    @staticmethod
    def getInstance():
        if TradingClock.__instance == None:
            TradingClock()
        return TradingClock.__instance

    def __init__(self):
        if TradingClock.__instance != None:
            raise Exception("Singleton")
        else:
            TradingClock.__instance = self

    mytz = pytz.timezone('Australia/Sydney') # tz.gettz('Australia/Sydney')  #
    __actual = datetime.datetime(year=1970, month=1, day=1, tzinfo=mytz)

    def __str__(self):
        return "Clock tuned to " + self.__actual.strftime("%d/%m/%Y, %H:%M:%S")

    @property
    def date(self):
        return self.__actual.date()

    @property
    def sync_datetime(self):
        return self.__actual

    @sync_datetime.setter
    def sync_datetime(self, value):
        if value.tzinfo is None:
            value = value.replace(tzinfo=self.mytz)
        self.__actual = value
        for i, callback in enumerate(self.change_callbacks):
            callback()

    change_callbacks = []

    def add_callback(self, func):
        self.change_callbacks.append(func)

    def istrading(self):
        # TODO: dirty dirty
        if not (TradingCalendar.is_trading_day(self.date) or TradingCalendar.is_partial_trading_day(self.date)):
            return False
        range = TradingCalendar.tradingtimes(self.date)
        return range[0].time() < self.sync_datetime.time() < range[-1].time()

    def set_day(self, value):
        daily_start = datetime.time(0, 0)
        setvalue = datetime.datetime.combine(value, daily_start)
        self.sync_datetime = setvalue
        return self.sync_datetime

    def roll_day(self):
        return self.set_day(TradingCalendar.add_trading_days(self.date, 1))


if __name__ == "__main__":
    clock = TradingClock.getInstance()

    times = [
        datetime.time(22, 6),
        datetime.time(22, 7),
        datetime.time(22, 8),
        datetime.time(22, 9),
        datetime.time(22, 10),
        datetime.time(22, 11),
        datetime.time(22, 12),
    ]
    dates = [clock.mytz.localize(datetime.datetime.combine(datetime.date.today(), time)) for time in times]

    print(dates[0])
