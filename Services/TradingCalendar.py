import datetime

import numpy as np
import pandas as pd
from workalendar.oceania.australia import NewSouthWales


class TradingCalendar():
    # https://www.marketbeat.com/stock-market-holidays/australia/

    auscal = NewSouthWales()
    normal_close = datetime.time(hour=16, minute=10)
    holidays = [
        datetime.date(2020, 12, 25),
        datetime.date(2020, 12, 28),

        # 2021
        datetime.date(2021, 1, 1),
        datetime.date(2021, 1, 26),
        datetime.date(2021, 4, 2),
        datetime.date(2021, 4, 5),
        datetime.date(2021, 4, 25),
        datetime.date(2021, 6, 14),
        datetime.date(2021, 12, 27),
        datetime.date(2021, 12, 28),

        # 2022
        datetime.date(2022, 1, 3),
        datetime.date(2022, 1, 26),
        datetime.date(2022, 4, 15),
        datetime.date(2022, 4, 18),
        datetime.date(2022, 4, 25),
        datetime.date(2022, 6, 13),
        datetime.date(2022, 12, 26),
        datetime.date(2022, 12, 27),
    ]

    partial_close = datetime.time(hour=14, minute=10)
    partial_holidays = [
        # 2020
        datetime.date(2020, 12, 24),
        datetime.date(2020, 12, 31),

        # 2021
        datetime.date(2021, 12, 24),
        datetime.date(2021, 12, 31),

        # 2022
        datetime.date(2022, 12, 23),
        datetime.date(2022, 12, 30)
    ]

    # TODO: Whether to skip, whether missing

    @staticmethod
    def is_trading_day(date):
        """
        :param date:
        :return: is_trading, is_full
        """
        if type(date) is datetime.datetime:
            date = date.date()
        weekday = date.isoweekday() < 6
        holiday = date in TradingCalendar.holidays
        partial = date in TradingCalendar.partial_holidays
        return (weekday and not holiday) or partial

    @staticmethod
    def is_partial_trading_day(date):
        if type(date) is datetime.datetime:
            date = date.date()
        return date in TradingCalendar.partial_holidays

    @staticmethod
    def add_trading_days(date, days):
        date_og = date
        if type(date) is datetime.datetime:
            date = date.date()

        count = 0
        added = 0
        sign = int(np.sign(days))
        while added < abs(days):
            date += datetime.timedelta(days=sign)
            if TradingCalendar.is_trading_day(date):
                added += 1
            count += 1
        return date_og + datetime.timedelta(days=count * sign)

    @staticmethod
    def tradingtimes(date, freq="5min"):
        # pd.date_range("2021-10-1 10:00", "2021-10-1 15:55", freq="5min")
        start = date.strftime("%Y-%m-%d") + " 10:00:00"

        if TradingCalendar.is_trading_day(date):
            end = date.strftime("%Y-%m-%d") + " 16:00:00"
        elif TradingCalendar.is_partial_trading_day(date):
            end = date.strftime("%Y-%m-%d") + " 14:30:00"
        else:
            raise ValueError(f"Not a trading date ({date})")

        # return pd.timedelta_range(start=start, end=end, freq=freq)
        return pd.date_range(start=start, end=end, freq=freq, tz='Australia/Sydney')


if __name__ == "__main__":
    weekend = datetime.datetime(2021, 1, 3)
    td = TradingCalendar.is_trading_day(weekend)
    assert (not td), "Weekend wrong"

    half_day = datetime.datetime(2021, 12, 31)
    td = TradingCalendar.is_trading_day(half_day)
    assert td, "half_day wrong"

    holiday = datetime.datetime(2021, 1, 1)
    td = TradingCalendar.is_trading_day(holiday)
    assert (not td), "holiday wrong"

    full_day = datetime.datetime(2021, 1, 7)
    td = TradingCalendar.is_trading_day(full_day)
    assert td, "full_day wrong"

    monday = datetime.datetime(2021, 1, 4)
    monday_p5 = TradingCalendar.add_trading_days(monday, 6)
