import datetime
import sys
from pathlib import Path
from shutil import copyfile

import numpy as np
import pandas as pd
from workalendar.oceania.australia import NewSouthWales

sys.path.append('..')

from Services.TradingClock import TradingClock
from Datasets.dllib import getDataframe, replace_empties
from Services.TradingCalendar import TradingCalendar as tcal
from Services.Datafactory import DataFactory

from _config import TICKERS_LEDGER


## Look into alpaac
#
# def next_working_day(sdate, cal):
#     addition = 1
#     while addition < 14:
#         nwd = sdate + datetime.timedelta(days=addition)
#         if cal.is_working_day(nwd):
#             return nwd
#         addition += 1
#     return sdate + datetime.timedelta(days=1)


# PYHON logging should replace this....
class Logger():
    """Write out to files"""
    __instance = None
    infos: list = []
    warnings: list = []
    errors: list = []
    created: datetime

    @staticmethod
    def getInstance():
        if Logger.__instance == None:
            Logger()
        return Logger.__instance

    def __init__(self):
        if Logger.__instance != None:
            raise Exception("Singleton")
        else:
            self.created = datetime.datetime.now()
            Logger.__instance = self

    @property
    def header(self):
        return f'RUN ({self.created.strftime("%m/%d/%Y, %H:%M:%S")})\n'

    def LogEvent(self, type: str, msg: str, consoleout: bool = True):
        if type == "ERROR":
            self.errors.append(msg)
        elif type == "WARN":
            self.warnings.append(msg)
        elif type == "INFO":
            self.infos.append(msg)
        if consoleout:
            print(f"{type}: {msg}")

    def WriteOut(self):
        with open("log_infos.txt", "a") as myfile:
            myfile.write(f"{self.header}")
            if len(self.infos) < 1:
                myfile.write("Nothing to display.")
            else:
                for msg in self.infos:
                    myfile.write(f"{msg}\n")
            myfile.write(f"\n\n")

        if len(self.errors) > 0:
            with open("log_errors.txt", "a") as myfile:
                myfile.write(f"{self.header}")
                for msg in self.errors:
                    myfile.write(f"{msg}\n")
                myfile.write(f"\n\n")

        if len(self.warnings) > 0:
            with open("log_warnings.txt", "a") as myfile:
                myfile.write(f"{self.header}")
                for msg in self.warnings:
                    myfile.write(f"{msg}\n")
                myfile.write(f"\n\n")


def scrape_new(ticker, period, start_date, end_date):
    """Scrapes new data to the current store"""
    logger = Logger.getInstance()
    datafactory = DataFactory.getInstance()

    # File locations
    csv_path = datafactory.getDataDir(period) + datafactory.symbol2file(ticker)
    record_exists = Path(csv_path).exists()

    # Attempt to find the date range
    record = None
    try:
        if record_exists:
            record = datafactory.loadSymbol(ticker)
            record_end_date = record.index[-1]
            daydelta = datetime.timedelta(days=1)
            start_date = max(start_date, (record_end_date + daydelta).date())

            # Can potentially skip
            dates_between = pd.date_range(start_date, end_date - daydelta, freq='d')
            dates_between_workdays = pd.Series(dates_between).transform(lambda x: tcal.is_trading_day(x))
            if (dates_between_workdays.empty) or (not dates_between_workdays.any()):
                logger.LogEvent("INFO", f"No dates to update for {ticker} {period}")
                return True
    except Exception as e:
        logger.LogEvent("ERROR", f"Error getting date ({ticker}, {period}): {e}, {type(e)}")

    # Attempt to scrape the data
    try:
        logger.LogEvent("INFO", f"Collecting {ticker} {period} from {start_date} to {end_date}")
        dataframe_dl = getDataframe(ticker, start_date, end_date, period, instant=False)
        if not dataframe_dl.empty:
            if record is None:
                # Failed to load
                if record_exists:
                    today = datetime.datetime.now()
                    copyfile(csv_path, f"{csv_path[:-4]} - Copy {today.month}-{today.day}{csv_path[-4:]}")

                dataframe_dl.to_csv(csv_path)
            else:
                dataframe_dl.to_csv(csv_path, mode='a', header=False)
        return True
    except Exception as e:
        logger.LogEvent("ERROR", f"Error downloading ({ticker}, {period}): {e}, {type(e)}")


def scrape_repair(ticker, period, start_date):
    """Aim to fill missing gaps. First aims for days. Then times"""
    logger = Logger.getInstance()
    datafactory = DataFactory.getInstance()

    daydelta = datetime.timedelta(days=1)
    cal = NewSouthWales()
    csv_path = datafactory.getDataDir(period) + datafactory.symbol2file(ticker)

    # Load the dataframe, get list of dates
    dataframe_full = datafactory.loadSymbol(ticker, period)

    dataframe_full = dataframe_full[~dataframe_full.index.duplicated()]
    dataframe_dates = pd.Series(dataframe_full.index).transform(lambda x: x.date())
    dataframe_full_dates = sorted([x for x in set(dataframe_dates) if x >= start_date])

    mytz = TradingClock.mytz


    # PT1: Are any dates missing
    try:
        prefix_dates = len(dataframe_full_dates)
        missing_dates = []
        for datei in range(1, len(dataframe_full_dates)):
            day1 = dataframe_full_dates[datei - 1]
            day2 = dataframe_full_dates[datei]
            missing_dates = missing_dates + [x.date() for x in pd.date_range(day1 + daydelta, day2 - daydelta, freq='d')
                                             if tcal.is_trading_day(x.date())]

        if len(missing_dates) > 0:
            # Combine missing dates to ranges
            missing_ranges = list(
                zip(missing_dates, [tcal.add_trading_days(missing_date, 1) for missing_date in missing_dates]))
            # zip(missing_dates, [next_working_day(missing_date, cal) for missing_date in missing_dates]))
            for datei in range(len(missing_ranges) - 2, -1, -1):
                c1, c2 = missing_ranges[datei]
                n1, n2 = missing_ranges[datei + 1]
                if c2+ datetime.timedelta(days=(0 if period == "5m" else 50)) >= n1:
                    missing_ranges.pop(datei + 1)
                    missing_ranges[datei] = (c1, n2)

            # Patch it up
            logger.LogEvent("INFO", f"Collecting missing dates for {ticker}  {period}")
            for missing_start, missing_end in missing_ranges:
                dataframe_patch = getDataframe(ticker, missing_start, missing_end, period, instant=False)
                if not dataframe_patch.empty:
                    before_dl = dataframe_full[:datetime.datetime(year=missing_start.year, month=missing_start.month,
                                                                  day=missing_start.day, tzinfo=mytz)]
                    after_dl = dataframe_full[
                               datetime.datetime(year=missing_end.year, month=missing_end.month, day=missing_end.day,
                                                 tzinfo=mytz):]
                    dataframe_full = pd.concat([before_dl, dataframe_patch, after_dl])
                else:
                    logger.LogEvent("WARN",
                                    f"Cannot find data for ({ticker}, {period}) between {missing_start}=>{missing_end} to patch data")

        else:
            logger.LogEvent("INFO", f"No missing dates for {ticker}  {period}")

        dataframe_dates = pd.Series(dataframe_full.index).transform(lambda x: x.date())
        dataframe_full_dates = sorted([x for x in set(dataframe_dates) if x >= start_date])
        postfix_dates = len(dataframe_full_dates)

        if prefix_dates < postfix_dates:
            # Over-write what we have saved
            dataframe_full.index.name = "Datetime"
            dataframe_full.to_csv(csv_path, index_label=dataframe_full.index.name)
    except Exception as e:
        logger.LogEvent("ERROR", f"Error fixing missing dates for ({ticker}, {period}): {e}, {type(e)}")
        return False, -1, -1

    # PT2: What is the content like ??
    try:
        missing_days_times = {}
        prefix_rows = len(dataframe_full)

        if period != "1d":
            # setup
            missing_cutoff = datetime.time(14, 00)
            if period == "5m":
                t_range = pd.Series(pd.date_range("10:00", "15:55", freq="5min")).transform(lambda x: x.time())
            else:
                raise ValueError(f"Period {period} not supported")

            # fill the missing_days_times dict
            for df_date in dataframe_full_dates:
                # List of times for the day
                df_dt = datetime.datetime(year=df_date.year, month=df_date.month, day=df_date.day, tzinfo=mytz)
                t_dataframe = pd.Series(dataframe_full[df_dt:df_dt + daydelta].index).transform(lambda x: x.time())

                # Are all of these times in the expected time range?
                missing_times = t_range[~t_range.isin(t_dataframe)]
                if tcal.is_partial_trading_day(df_date):
                    missing_times = [x for x in missing_times if x < missing_cutoff]
                if len(missing_times) > 0:
                    missing_days_times[df_date] = missing_times

            # If there is any data missing, try and fix
            missing_times_dates = list(missing_days_times.keys())
            if len(missing_times_dates) > 0:
                # Combine missing dates to ranges
                missing_ranges = list(zip(missing_times_dates,
                                          [tcal.add_trading_days(missing_date, 1) for missing_date in
                                           missing_times_dates]))
                for datei in range(len(missing_ranges) - 2, -1, -1):
                    c1, c2 = missing_ranges[datei]
                    n1, n2 = missing_ranges[datei + 1]
                    # Give this one a bit of room, there are more missing
                    if c2 + datetime.timedelta(days=2) >= n1:
                        missing_ranges.pop(datei + 1)
                        missing_ranges[datei] = (c1, n2)

                logger.LogEvent("INFO", f"Collecting missing times for {ticker} {period}")
                for missing_start, missing_end in missing_ranges:
                    dataframe_patch = getDataframe(ticker, missing_start, missing_end, period, instant=False)
                    patch_dates = set(pd.Series(dataframe_patch.index).transform(lambda x: x.date()))
                    for patch_date in sorted(list(patch_dates)):
                        # Check if the data wasn't added when grouping ranges
                        if patch_date in missing_days_times.keys():
                            missing_dtimes = pd.Series([datetime.datetime.combine(patch_date, mdt) for mdt in
                                                        missing_days_times[patch_date]]).transform(
                                lambda x: x.tz_localize(mytz))
                            times_found = missing_dtimes[missing_dtimes.isin(dataframe_patch.index)]
                            for found_time in times_found:
                                # patcher = dataframe_patch.loc[found_time]
                                before_dl = dataframe_full[dataframe_full.index < found_time]
                                patcher = pd.DataFrame([dataframe_patch.loc[found_time].values],
                                                       columns=[xx for xx in dataframe_full.columns if
                                                                not xx == "Datetime"],
                                                       index=pd.DatetimeIndex([found_time]))
                                after_dl = dataframe_full[dataframe_full.index > found_time]
                                dataframe_full = pd.concat([before_dl, patcher, after_dl])

        # Check that some changes were actually made...
        fixed_rows = len(dataframe_full) - prefix_rows
        if fixed_rows > 0:
            logger.LogEvent("INFO", f"Patched {fixed_rows} rows successfully for {ticker} {period}")
            if not dataframe_full.index.is_monotonic:
                dataframe_full = dataframe_full.index_sort()
                logger.LogEvent("ERROR", f"Index not sorted properly {ticker}")
            dataframe_full.index.name = "Datetime"
            dataframe_full.to_csv(csv_path)
        else:
            logger.LogEvent("WARN", f"No missing time patched for {ticker} {period}")
    except Exception as e:
        logger.LogEvent("ERROR", f"Error fixing missing times for ({ticker}, {period}): {e}, {type(e)}")
        return False, -1, -1

    # Leftovers
    fixed_dates = postfix_dates - prefix_dates
    outstanding_dates = len(missing_dates) - fixed_dates
    fixed_times = fixed_rows
    outstanding_times = sum([len(x) for x in missing_days_times.values()]) - fixed_times
    print(fixed_dates)

    return True, outstanding_dates, outstanding_times


if __name__ == "__main__":
    """Runs scheduled data scrapes and repairs. Executed by batch script daily"""
    # TODO: Change ledger to reflect periods (sep 5m / 1d)
    print("DATA SCRAPER UTILITY")

    # Parse args
    testing = False
    for arg in sys.argv:
        if arg == "-test":
            print("-test detected")
            testing = True
    print("")

    # Setup
    logger = Logger.getInstance()
    datafactory = DataFactory.getInstance()

    # lEDGER DETAILS
    ledger_path = TICKERS_LEDGER
    tickers_ledger = pd.read_csv(ledger_path)
    dtf = "%d/%m/%Y"  # 20/12/2020


    def empty_col(val):
        if type(val) is not float:
            return True
        return not np.isnan(val)


    # Tickers scheduled for collection
    coll_dates = tickers_ledger["COLL_LAST"].transform(
        lambda x: datetime.datetime.strptime(x, dtf).date() if empty_col(x) else datetime.date(1900, 1, 1))
    coll_freq = tickers_ledger["COLL_FREQ"].transform(lambda x: datetime.timedelta(days=x))
    coll_due_dates = pd.Series([x + y for x, y in zip(coll_dates, coll_freq)])
    coll_df = tickers_ledger[coll_due_dates <= datetime.datetime.now().date()]
    coll_df_tickers = list(coll_df["TICKER"])

    # Tickers scheduled for repair
    repair_dates = tickers_ledger["REPAIR_LAST"].transform(
        lambda x: datetime.datetime.strptime(x, dtf).date() if empty_col(x) else datetime.date(1900, 1, 1))
    repair_freq = tickers_ledger["REPAIR_FREQ"].transform(lambda x: datetime.timedelta(days=x))
    repair_due_dates = pd.Series([x + y for x, y in zip(repair_dates, repair_freq)])
    repair_df = tickers_ledger[(repair_due_dates <= datetime.datetime.now().date()) & (tickers_ledger.CAT <= 3)]
    repair_df_tickers = list(repair_df["TICKER"])

    # Download
    periods = ["1d"]  # if not testing else ["5m"]
    for period in periods:
        if period == "5m":
            lookback = datetime.timedelta(days=60)  # if not testing else datetime.timedelta(days=60)
            data_path = datafactory.DATA_DIRECTORY
        elif period == "1d":
            lookback = datetime.timedelta(days=365)
            data_path = datafactory.DATA_DIRECTORY_DAILY
        else:
            raise AssertionError("Period unrecognised")

        # Date range
        end_date = datetime.date.today()
        if datetime.datetime.now().hour >= 17:
            end_date += datetime.timedelta(days=1)
        else:
            lookback -= datetime.timedelta(days=1)
        start_date = end_date - lookback

        # Scrape new data in
        print(f"SCRAPING ({len(coll_df_tickers)}):")
        for ticker in coll_df_tickers:
            try:
                print(f"{ticker} ({coll_df_tickers.index(ticker) + 1}/{len(coll_df_tickers)})")
                success = scrape_new(ticker, period, start_date, end_date)
                tickers_ledger.loc[tickers_ledger.TICKER == ticker, "STATUS"] = "GOOD" if success else "BAD"
                if success:
                    tickers_ledger.loc[
                        tickers_ledger.TICKER == ticker, "COLL_LAST"] = datetime.datetime.now().date().strftime(dtf)
                tickers_ledger.to_csv(ledger_path, index=False)
            except Exception as e:
                logger.LogEvent("ERROR", f"Error scraping ({ticker}, {period}): {e}, {type(e)}")

        # Repair old data
        print(f"REPAIRING ({len(repair_df_tickers)}):")
        for ticker in repair_df_tickers:
            try:
                print(f"{ticker} ({repair_df_tickers.index(ticker) + 1}/{len(repair_df_tickers)})")
                success, missing_dates, missing_times = scrape_repair(ticker, period, start_date)
                tickers_ledger.loc[tickers_ledger.TICKER == ticker, "STATUS"] = "GOOD" if success else "BAD"
                if success:
                    tickers_ledger.loc[
                        tickers_ledger.TICKER == ticker, "REPAIR_LAST"] = datetime.datetime.now().date().strftime(dtf)
                    if period == "5m":
                        tickers_ledger.loc[tickers_ledger.TICKER == ticker, "MISSING_DATES"] = missing_dates
                        tickers_ledger.loc[tickers_ledger.TICKER == ticker, "MISSING_TIMES"] = missing_times
                tickers_ledger.to_csv(ledger_path, index=False)
            except Exception as e:
                logger.LogEvent("ERROR", f"Error repairing ({ticker}, {period}): {e}, {type(e)}")

        if period == "5m":
            to_replace = set(coll_df_tickers + repair_df_tickers)
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
                    logger.LogEvent("ERROR", f"Error replacing empties for ticker {ticker} - {e} ")
                finally:
                    DataFactory.repairedDFS = DFS
        DataFactory.repaired = False

    if not testing:
        logger.WriteOut()

    # Fix the schedule so things aren't packed to a single day
    tickers_ledger_og = tickers_ledger.copy()
    earliest = datetime.datetime.now().date() + datetime.timedelta(days=1)
    for scrape_style in ["COLL", "REPAIR"]:
        # Tickers scheduled for collection
        coll_dates = tickers_ledger[f"{scrape_style}_LAST"].transform(
            lambda x: datetime.datetime.strptime(x, dtf).date() if empty_col(x) else datetime.date(1900, 1, 1))
        coll_freq = tickers_ledger[f"{scrape_style}_FREQ"].transform(lambda x: datetime.timedelta(days=x))
        coll_due_dates = pd.Series([x + y for x, y in zip(coll_dates, coll_freq)])
        coll_dues_og = pd.DataFrame(coll_due_dates.value_counts(), columns=["Count"]).sort_index()

        # Full coll due list
        full_dates_range = pd.date_range(earliest, max(coll_dues_og.index), freq='d')
        coll_dues_empty_dates = full_dates_range[~full_dates_range.isin(coll_dues_og.index)]
        coll_dues_empty = pd.DataFrame([0] * len(coll_dues_empty_dates), columns=["Count"],
                                       index=coll_dues_empty_dates.date)
        coll_dues_all = pd.concat([coll_dues_og, coll_dues_empty]).sort_index()

        # Iterate over
        for coll_due_date, coll_num in zip(coll_dues_og.index, coll_dues_og.Count):
            tickers_to_move = tickers_ledger[coll_due_dates == coll_due_date]
            mindue = coll_dues_all.loc[:coll_due_date].values.min()
            currdue = coll_dues_all.loc[coll_due_date, 'Count']
            while (mindue + 1 < currdue):
                # which date has the maximum availability
                min_assigned = coll_dues_all.index[coll_dues_all.loc[:coll_due_date].values.argmin()]

                # Select a ticker, remove it
                tickers_to_move_mask = tickers_to_move["CAT"] == max(tickers_to_move["CAT"].values)
                randsample = tickers_to_move.sample(1).TICKER
                ticker_to_move = randsample.values[0]

                # Change the ledger
                ticker_freq = int(tickers_ledger.loc[tickers_ledger.TICKER == ticker_to_move, f"{scrape_style}_FREQ"])
                ticker_mask = tickers_ledger.TICKER == ticker_to_move
                ticker_newdate = (min_assigned - datetime.timedelta(days=ticker_freq)).strftime(dtf)
                tickers_ledger.loc[ticker_mask, f"{scrape_style}_LAST"] = ticker_newdate

                # reassign
                coll_dues_all.loc[min_assigned] += 1
                coll_dues_all.loc[coll_due_date] -= 1
                tickers_to_move = tickers_to_move.drop(randsample.index[0])

                # exit condition
                mindue = coll_dues_all.loc[:coll_due_date].values.min()
                currdue = coll_dues_all.loc[coll_due_date, 'Count']

        # Check the integrity
        dates_new = pd.to_datetime(tickers_ledger[f"{scrape_style}_LAST"], format=dtf)
        dates_og = pd.to_datetime(tickers_ledger_og[f"{scrape_style}_LAST"], format=dtf)
        if (dates_new <= dates_og).all():
            tickers_ledger.to_csv(ledger_path, index=False)
