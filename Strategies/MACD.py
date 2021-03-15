import datetime

import datetime
import numpy as np
import pandas as pd
import talib

from Components.Manager import Manager
from Services.Datafactory import DataFactory
from Services.TradingClock import TradingClock
from Strategies.IStrategy import IStrategy
from Utils import Indicators
from ibapi.contract import Contract
from ibapi.order import Order

# TODO: day plotting

class MACD(IStrategy):
    ''' The idea behind this is to follow the smart money and catch
    short term trends'''

    def __init__(self, manager, name, symbols, properties):

        self.days_required_5m = None
        #self.days_required_1d = None
        self.ema_short_days = None
        self.ema_long_days = None
        self.signal_line_days = None

        super().__init__(manager, name, symbols, properties,
                         required=['days_required_5m',
                                   #'days_required_1d',
                                   'ema_short_days', 'ema_long_days', 'signal_line_days'],
                         )#mainBarsize="1day")

    def setup(self):
        # contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate, keepUpToDate, chartOptions
        # Create a contract object
        for symbol in self.symbols:
            contract = Contract()
            contract.symbol = symbol
            contract.secType = "STK"

            # Make a data request
            self.reqHistoricalData(contract, "", f"{self.days_required_5m+1} D", "5 min", "BID_ASK", 0, 1, True, [])
            #self.reqHistoricalData(contract, "", f"{self.days_required_1d+5} D", "1 day", "BID_ASK", 0, 1, True, [])

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
        self.update(forcedexit=True)

    def update(self, forcedexit=False):

        for symbol in self.symbols:
            data5m = self[symbol]
            #data1d = self[symbol+"1day"]

            nrows, ncols = data5m.shape
            if nrows < 6 * 12 * self.ema_long_days:
                continue

            try:
                # Long term data
                short_avg = Indicators.avgPrice(data5m)

                ema12 = talib.EMA(short_avg, 72 * self.ema_short_days)
                ema26 = talib.EMA(short_avg, 72 * self.ema_long_days)
                macd = ema12 - ema26
                signal = talib.EMA(macd, 72 * self.signal_line_days)

                #self.indicators[f'ema {12}'] = ema12
                #self.indicators[f'ema {26}'] = ema26
                self.indicators['macd'] = (macd, {"panel": 2})
                self.indicators['signal'] = (signal, {"panel": 2})

                if forcedexit:
                    self.closePosition(symbol, 0)
                    continue

                trending_up = False
                trending_down = False

                lookback = 12 * 1
                for i in range(1, lookback+1):

                    if macd[-i - 1] <= signal[-i - 1] and macd[-i] > signal[-i]:
                        trending_up = True

                    if macd[-i - 1] >= signal[-i - 1] and macd[-i] < signal[-i]:
                        trending_down = True


                if trending_up ^ trending_down:
                    invol, inval = self.manager.account.getPosition(symbol)
                    if trending_up and not invol:
                        cash = self.manager.account.cash
                        minval = 1000
                        current_price = data5m.Open[-1]
                        if minval <= cash:
                            self.openPosition(symbol, cash // current_price)

                    if trending_down and invol:
                        self.closePosition(symbol, invol)
            except Exception as e:
                self.logger.exception(e)


if __name__ == "__main__":
    DataFactory.repaired = True
    clock, datafactory = TradingClock.getInstance(), DataFactory.getInstance()
    clock.sync_datetime = datetime.datetime.now()

    m = Manager()
    s = MACD(m, "SA", ["ASIA"], {"days_required_5m": 31, "days_required_1d": 200})
    s.update()
    print('asdf')
