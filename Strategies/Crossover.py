import datetime

import numpy as np
import pandas as pd
import talib
from scipy.signal import savgol_filter

from Strategies.IStrategy import IStrategy
from Utils import Indicators
from ibapi.contract import Contract
from ibapi.order import Order


class Crossover(IStrategy):
    def __init__(self, manager, name, symbols, properties):

        self.days_required = None
        self.sma_fast = None
        self.sma_med = None
        self.sma_slow = None

        super().__init__(manager, name, symbols, properties,
                         required=['days_required', 'sma_fast', 'sma_med', 'sma_slow'])

    def setup(self):
        assert self.sma_fast < self.sma_med < self.sma_slow, "Periods don't ascend"

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
            data = self[symbol]
            avg_price = Indicators.avgPrice(data)

            nrows, ncols = data.shape
            if nrows < 12 * 6 * self.sma_slow + 12:
                continue

            savgol_days = 1
            savgol_window = (72 * savgol_days) + 1
            asset_data = pd.Series(savgol_filter(avg_price, savgol_window, 3), index=avg_price.index)

            sma_fast = talib.SMA(avg_price, timeperiod=12 * 6 * self.sma_fast)
            sma_med = talib.SMA(avg_price, timeperiod=12 * 6 * self.sma_med)
            sma_slow = talib.SMA(avg_price, timeperiod=12 * 6 * self.sma_slow)

            # self.indicators['filter'] = asset_data
            self.indicators[f'sma {self.sma_fast}'] = (sma_fast, {})
            self.indicators[f'sma {self.sma_med}'] = (sma_med, {})
            self.indicators[f'sma {self.sma_slow}'] = (sma_slow, {})

            sma_fast_last = sma_fast[self.clock.sync_datetime - datetime.timedelta(hours=1):]
            sma_med_last = sma_med[self.clock.sync_datetime - datetime.timedelta(hours=1):]
            sma_slow_last = sma_slow[self.clock.sync_datetime - datetime.timedelta(hours=1):]

            current_price = avg_price[-1]

            trending_up = (np.array([sma_slow_last < sma_med_last]) & np.array([sma_med_last < sma_fast_last])).all()
            trending_down = (np.array([sma_fast_last < sma_med_last]) & np.array([sma_med_last < sma_slow_last])).all()

            if trending_up:
                cash = self.manager.account.cash
                minval = 1000
                if minval <= cash:
                    self.openPosition(symbol, cash // current_price)

            elif trending_down:
                invol, inval = self.manager.account.getPosition(symbol)
                if invol:
                    self.closePosition(symbol, invol)
