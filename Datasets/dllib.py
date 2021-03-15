import datetime
import sys
import time

import pandas as pd
import yfinance as yf

from Services.MyLogger import MyLogger

sys.path.append('..')

from Services.TradingCalendar import TradingCalendar as tcal


# TODO: Fix these two post move

def getDataframe(ticker: str, start_date: datetime, end_date: datetime, period: str, instant=True) -> pd.DataFrame:
    """Download a dataframe in segments from yahoo finance."""
    # logger = Logger.getInstance()

    print(f"Download called for {ticker} with arguments {start_date} -> {end_date}")

    dataframe = pd.DataFrame()
    time_spread = datetime.timedelta(days=133) if period == "1d" else datetime.timedelta(days=31)

    ''' TODO: This is naive, what if the data fails consistently? Missing data doesn't throw an exception'''
    while (True):
        # Exit condition
        if (start_date >= end_date):
            break

        try:
            to_date = min(start_date + time_spread, end_date)
            dataframe_dl = yf.download(ticker,
                                       start=start_date.strftime("%Y-%m-%d"),
                                       end=to_date.strftime("%Y-%m-%d"),
                                       interval=period)
            if not instant: # input should be time not boolean
                time.sleep(3)

            dataframe = pd.concat([dataframe, dataframe_dl])
            if dataframe.empty:
                pass  # logger.LogEvent("WARN", f"No data for {ticker} from {start_date}->{end_date}\n")
        except Exception as e:
            pass  # logger.LogEvent("ERROR", f"Error downloading {start_date}->{end_date}: {e}, {type(e)}\n")
        else:
            start_date = start_date + time_spread

    # May need to transofmr the index to fit the desired format
    if period == "1d":
        def transform_date(date):
            dt = pd.to_datetime(date)
            dt = dt + pd.Timedelta(hours=16)  # EOD
            return dt.tz_localize("Australia/Sydney")

        new_index = pd.Series(dataframe.index).transform(lambda x: transform_date(x))
        dataframe.index = pd.Index(new_index, name="Datetime")

    if (not dataframe.empty) and (dataframe.index.name != "Datetime"):
        # logger.LogEvent(f"WARN", f"Index name not right for {ticker}, attempting fix")
        dataframe.index.name = "Datetime"

    return dataframe


def replace_empties(data, goal=None):
    logger = MyLogger.getLogger("RepUtil")

    if goal is not None and goal < data.index[-1]:
        logger.warn(f"Goal date {goal} is pre-data end {data.index[-1]}, resetting")
        goal = data.index[-1]

    dates = sorted(list(set(pd.Series(data.index).transform(lambda x: x.date()))))
    date = dates[0]
    end_date = dates[-1] if goal is None else goal.date()
    period = min([abs(d1 - d2) for d1, d2 in zip(data.index[1:], data.index[:-1])])

    while date <= end_date:
        if tcal.is_partial_trading_day(date) or tcal.is_trading_day(date):


            #TODO: Bug - min period changed if get a partial bar


            if period > datetime.timedelta(minutes=5):
                # TODO: Bit ugly.... shoed in
                missing_ranges = []
                if date not in dates:
                    missing_ranges = [[data.index[0].replace(year=date.year, month=date.month, day=date.day)]]
            else:
                ttimes = tcal.tradingtimes(date)
                if goal is None:
                    missing_times = ttimes[~ttimes.isin(data.index)]
                else:
                    missing_times = ttimes[~ttimes.isin(data.index) & (ttimes <= goal)]
                missing_ranges = []

                if len(missing_times):
                    # Blocks of missing data
                    missing_ranges.append([missing_times[0]])
                    for missing_time in missing_times[1:]:
                        previous = missing_ranges[-1][-1]

                        next_span = missing_time - previous
                        if next_span != period:
                            missing_ranges.append([missing_time])
                        else:
                            missing_ranges[-1].append(missing_time)

            # chuck repeated in there
            for missing_range in missing_ranges:
                try:
                    before = data[data.index < missing_range[0]]
                    after = data[data.index > missing_range[-1]]

                    previous = before.iloc[-1]

                    patch = pd.DataFrame({"Open": previous.Close, "High": previous.Close, "Low": previous.Close,
                                          "Close": previous.Close, "Adj Close": previous.Close, "Volume": 0},
                                         index=missing_range)


                    data = pd.concat([before, patch, after])
                    data = data[~data.index.duplicated(keep='last')]
                except Exception as e:
                    print(f"Repair failed for {e}")
        date += datetime.timedelta(days=1)
    return data


if __name__ == "__main__":
    from Services.Datafactory import DataFactory
    from Services.TradingClock import TradingClock

    tclock = TradingClock.getInstance()
    tclock.sync_datetime = datetime.datetime(
                            year=2021,
                            month=2,
                            day=25,
                            hour=12,
                            minute=10,
                            tzinfo=tclock.mytz)


    DataFactory.repaired = True
    DataFactory.live_data = True

    datafac = DataFactory.getInstance()
    data = datafac.loadSymbol("FRX")
    data = replace_empties(data)

    #3722

    print(data)
