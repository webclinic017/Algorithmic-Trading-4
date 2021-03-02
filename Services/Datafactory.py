import datetime

import pandas as pd

from Datasets.dllib import replace_empties, getDataframe
from Services.MyLogger import MyLogger
from Services.TradingClock import TradingClock


class DataFactory:
    __instance = None
    __data_root = "C:\\Users\\liamd\\Documents\\Project\\AlgoTrading\\Datasets\\"
    __data_folder = "CSV\\"
    __data_folder_repair = "CSV_REPAIR\\"
    __data_daily_folder = "CSV_DAILY\\"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S%z"

    repaired = False
    live_data = False

    @property
    def DATA_DIRECTORY(self):
        return self.__data_root + self.__data_folder

    @property
    def DATA_DIRECTORY_REPAIR(self):
        return self.__data_root + self.__data_folder_repair

    @property
    def DATA_DIRECTORY_DAILY(self):
        return self.__data_root + self.__data_daily_folder

    @staticmethod
    def getInstance():
        if DataFactory.__instance == None:
            DataFactory()
        return DataFactory.__instance

    prejack_symbols = []

    def __init__(self):
        if DataFactory.__instance != None:
            raise Exception("Singleton")
        else:
            self.logger = MyLogger.getLogger("DataFac")
            DataFactory.__instance = self

    def symbol2file(self, symbol):
        return symbol.replace(".AX", "") + ".csv"

    def file2symbol(self, filename):
        return filename[:-4]

    def getDataDir(self, barsize):
        barsize = barsize.upper()

        barsizeunits = [
            "SEC", "MIN", "HOUR",
            "DAY", "WEEK", "MONTH"
        ]
        barsizeunits_abbr = [
            "S", "M", "H",
            "D", "W", "MO"
        ]

        # TODO: barsize
        if barsize == "5 MIN" or barsize == "5M":
            dir = self.DATA_DIRECTORY if not self.repaired else self.DATA_DIRECTORY_REPAIR
        elif barsize == "1 DAY" or barsize == "1D":
            dir = self.DATA_DIRECTORY_DAILY
        else:
            raise ValueError(f"barsize {barsize} not recognised; use either \"5 M\" or \"1 D\"")
        return dir

    datadict = {}

    def _getkey(self, symbol, barsize):
        return symbol + "_" + barsize.replace(" ", "_")

    def loadFile(self, name, barsize="5 min"):
        try:
            # need smallest time scale data
            # if barsize != "5 min":
            #     self.loadFile(name, barsize="5 min")

            # todo: standardise format
            symbol = self.file2symbol(name)
            dd_key = self._getkey(symbol, barsize)#symbol + "_" + barsize.replace(" ", "_")

            if not (dd_key in self.datadict.keys()):
                dir = self.getDataDir(barsize)
                data = pd.read_csv(dir + name, index_col=0)
                data.index = pd.DatetimeIndex(
                    pd.Series(data.index).apply(lambda x: pd.to_datetime(x).tz_convert(TradingClock.mytz)))
                self.datadict[dd_key] = data

            if self.live_data:
                # Check where the data is up to, do we need to download new data?
                start = self.datadict[dd_key].index[-1]
                if start < TradingClock.getInstance().sync_datetime and start < TradingClock.getInstance().sync_datetime.replace(hour=16, minute=0):
                    start_date = start.date() - datetime.timedelta(days=1)
                    end_date = TradingClock.getInstance().date + datetime.timedelta(days=1)

                    # TODO: Case inconsistencies
                    new = getDataframe(symbol + '.AX', start_date, end_date, period="5m")
                    nrows, ncols = new.shape
                    if nrows:
                        new.index = pd.DatetimeIndex(
                            pd.Series(new.index).apply(lambda x: pd.to_datetime(x).tz_convert(TradingClock.mytz)))

                        if start.time().minute % 5 != 0 or start.time().second != 0:
                            new = pd.concat([self.datadict[dd_key].iloc[:-1], new])
                        else:
                            new = pd.concat([self.datadict[dd_key], new])

                        # updated data
                        if barsize=="1 day":
                            new = new[~(pd.Series(new.index).transform(lambda x: x.date()).duplicated(keep='last')).values]
                        else:
                            new = new[~new.index.duplicated(keep='last')]

                        if self.repaired:
                            new = replace_empties(new, goal=new.index[-1])
                        self.datadict[dd_key] = new


            return self.datadict[dd_key]
        except Exception as e:
            raise InterruptedError(f"Failed to load {name} - {e}")

    def loadSymbol(self, symbol, barsize="5 min"):
        return self.loadFile(self.symbol2file(symbol), barsize)


    @staticmethod
    def clear():
        DataFactory.datadict = {}

    def datesSpread(self, barsize="5 min"):
        '''Get the earliest and latest dates where data exists'''

        try:
            if not len(self.datadict):
                if not len(self.prejack_symbols):
                    self.prejack_symbols = ["VAS", "NDQ"]

                for prejack_symbol in self.prejack_symbols:
                    self.loadSymbol(prejack_symbol, barsize=barsize)
        except:
            print("WARN: failed pre-jack")

        earliest = datetime.datetime.now().date()
        latest = datetime.datetime(year=1900, month=1, day=1).date()

        if len(self.datadict.values()) < 1:
            tearliest = earliest
            earliest = latest
            latest = tearliest
        else:
            for dictdata in self.datadict.values():
                earliest = min(dictdata.index[0].date(), earliest)
                latest = max(dictdata.index[-1].date(), latest)
        # return pd.date_range(earliest, latest, freq='d').date
        return earliest, latest

    def getLatestPrice(self, symbol, important=True):
        # TODO: What is best for this?
        if self._getkey(symbol, "5 min") in self.datadict.keys():
            data = self.loadSymbol(symbol)
        else:
            data = self.loadSymbol(symbol, barsize="1 day")

        clock = TradingClock.getInstance()
        try:
            return data.loc[clock.sync_datetime, "Close"]
        except Exception as e:
            #pricerow = data.loc[:clock.sync_datetime].iloc[-1]
            pricerow = data.loc[data.index < clock.sync_datetime].iloc[-1]
            datetime1 = datetime.datetime.combine(clock.date, clock.sync_datetime.time())
            datetime2 = datetime.datetime.combine(pricerow.name.date(), pricerow.name.time())
            time_elapsed = datetime1 - datetime2

            if important:
                self.logger.debug(f"Time missed for {symbol} by {time_elapsed}")
                if pricerow.name.date() != clock.date:
                    pass  # raise Exception(f"too much data missing {clock.sync_datetime}")
            else:
                self.logger.debug(f"Time missed for {symbol} by {time_elapsed}")

            return pricerow.Close


if __name__ == "__main__":
    DataFactory.repaired = True
    DataFactory.live_data = True
    df = DataFactory.getInstance()
    clock = TradingClock.getInstance()
    clock.sync_datetime = datetime.datetime.now()

    data = df.loadSymbol("VAS")
