import datetime

import numpy as np
import pandas as pd
import talib
from scipy.signal import savgol_filter

from Components.Manager import Manager
from Services.Datafactory import DataFactory
from Services.TradingClock import TradingClock
from Strategies.IStrategy import IStrategy
from Utils import Indicators
from ibapi.contract import Contract
from ibapi.order import Order


class CrystalV3(IStrategy):
    ''' The idea behind this is to follow the smart money and catch
    short term trends'''

    def __init__(self, manager, name, symbols, properties):

        self.days_required = None

        self.ma_days = None
        self.ma_long_days = None

        self.buy_volume_sigma = None,
        self.sell_volume_sigma = None

        self.positive_sigma = None
        self.negative_sigma = None

        super().__init__(manager, name, symbols, properties,
                         required=['days_required', 'ma_days',
                                   'buy_volume_sigma', 'sell_volume_sigma',
                                   'ma_long_days', 'positive_sigma', 'negative_sigma'])

    def setup(self):
        # contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate, keepUpToDate, chartOptions
        # Create a contract object
        for symbol in self.symbols:
            contract = Contract()
            contract.symbol = symbol
            contract.secType = "STK"

            # Make a data request
            self.reqHistoricalData(contract, "", f"{self.days_required} D", "5 min", "BID_ASK", 0, 1, True, [])

    def openPosition(self, symbol, volume):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"

        order = Order()
        order.action = "BUY"
        order.totalQuantity = volume
        order.orderType = "MKT"

        self.placeOrder(contract, order)

    def closePosition(self, symbol, volume):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"

        order = Order()
        order.action = "SELL"
        order.totalQuantity = volume
        order.orderType = "MKT"

        self.placeOrder(contract, order)

    def closeall(self):
        for symbol in self.symbols:
            self.closePosition(symbol, 0)

    def update(self):

        for symbol in self.symbols:
            self.logger.debug(f"Update called for {symbol} ({self.name}) at {datetime.datetime.now()}")

            data = self[symbol]

            nrows, ncols = data.shape
            if nrows < 12 * 6 * self.ma_long_days + 12:
                continue

            self.logger.debug(f"latest data for {symbol} ({self.name}) is {data.index[-1]}")

            avg_price = Indicators.avgPrice(data)
            savgol_window = (3 * 12) + 1
            asset_data = pd.Series(savgol_filter(avg_price, savgol_window, 3), index=avg_price.index)

            sma = talib.SMA(asset_data, timeperiod=12 * 6 * self.ma_days)
            wma = talib.WMA(asset_data, timeperiod=12 * 6 * self.ma_days)

            std = np.std(avg_price.values[:-12 * 6 * self.ma_long_days])
            sma_long = talib.SMA(asset_data, timeperiod=12 * 6 * self.ma_long_days)
            sma_long_plus = sma_long + self.positive_sigma * std
            sma_long_minus = sma_long - self.negative_sigma * std

            # self.indicators['filter'] = asset_data
            self.indicators[f'sma {self.ma_days}'] = (sma, {})
            self.indicators[f'wma {self.ma_days}'] = (wma, {})
            self.indicators['sma_long+'] = (sma_long_plus, {})
            self.indicators['sma_long-'] = (sma_long_minus, {})

            trending_up = False
            trending_down = False

            lookback = 12 * 1
            for i in range(1, lookback + 1):

                if sma[-i - 1] <= wma[-i - 1] and sma[-i] > wma[-i]:
                    trending_up = True

                if sma[-i - 1] >= wma[-i - 1] and sma[-i] < wma[-i]:
                    trending_down = True
            self.openPosition(symbol, 1)
            # volume = data.Volume  # [-72*self.ma_long_days:]
            # volume_std = np.std(volume)
            # try:
            #     volume_med = np.median([v for v in volume if v])
            #     volume_avg = np.average([v for v in volume if v])
            # except:
            #     volume_med = 0
            #     volume_avg = 0


            # invol, inval = self.manager.account.getPosition(symbol)
            # if pd.Series(volume[-lookback:] > (volume_avg + self.buy_volume_sigma * volume_std)).any():
            #     if avg_price[-1] < sma_long_minus[-1]:
            #         if not invol:
            #             # if current_price < sma_long_plus[-1]:
            #             goal = (self.manager.account.cash / 10) // 1
            #             minval = 1000
            #             if goal > minval:
            #                 self.openPosition(symbol, goal // asset_data.values[-1])
            #
            # if pd.Series(volume[-lookback:] > (volume_avg + self.sell_volume_sigma * volume_std)).any():
            #     if avg_price[-1] > sma_long_plus[-1]:
            #         if invol:
            #             self.closePosition(symbol, invol)

            # lookback = 12 * 1
            # for i in range(1, lookback):
            #
            #     if ma[-i - 1] <= sma_long_minus[-i - 1] and ma[-i] > sma_long_minus[-i]:
            #         lower_cross = True
            #
            #     if ma[-i - 1] >= sma_long_plus[-i - 1] and ma[-i] < sma_long_plus[-i]:
            #         upper_cross = True
            #
            #
            # invol, inval = self.manager.account.getPosition(symbol)
            # if lower_cross ^ upper_cross:
            #     if lower_cross:
            #         if not invol:
            #                 #if current_price < sma_long_plus[-1]:
            #                 goal = self.manager.account.cash // 2
            #                 minval = 1000
            #                 if goal > minval:
            #                     self.openPosition(symbol, goal // asset_data.values[-1])
            #     if upper_cross:
            #         if invol:
            #                 self.closePosition(symbol, invol)


if __name__ == "__main__":
    DataFactory.repaired = True
    clock, datafactory = TradingClock.getInstance(), DataFactory.getInstance()
    clock.sync_datetime = datetime.datetime.now()

    m = Manager()
    s = CrystalV3(m, "SA", [], {"ma_days": 1, "ma_long_days": 1, "positive_sigma": 0.25, "negative_sigma": 0})

    print('asdf')
