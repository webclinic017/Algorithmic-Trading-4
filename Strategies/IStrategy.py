import logging
import uuid
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from Components.Manager import Manager
from Services.MyLogger import MyLogger
from Services.TradingClock import TradingClock


class IStrategy(ABC):
    # @property
    # def datas(self):
    #     return self.__symbols

    def __init__(self, manager, name, symbols, properties, required=[], mainBarsize=""):
        self.logger = MyLogger.getLogger(name, file=f"{name}.log", level=logging.INFO)
        self.clock = TradingClock.getInstance()
        self.manager: Manager = manager
        self.name = name
        self.id = uuid.uuid1()
        self.clock = TradingClock.getInstance()
        self.symbols = symbols
        self.mainBarsize = mainBarsize

        # Check properties
        self.__dict__ = {**self.__dict__, **properties}
        assert \
            all([rp in self.__dict__.keys() and self.__dict__[rp] is not None for rp in required]), \
            f"Missing required properties {[rp for rp in required if (rp not in self.__dict__.keys()) or (self.__dict__[rp] is None)]}"

        self.__symbols = {}  # map symbol to datas
        self.__requests = {}  # map requests to symbol

        self.indicators = {}

        # Call abstract setup method
        self.setup()

    def __getitem__(self, symbolkey):
        '''Index the strategy for ticker data'''
        return self.__symbols[symbolkey]

    def reqHistoricalData(self, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate,
                          keepUpToDate, chartOptions):
        '''Request historical data and map id to ticker'''
        reqId = self.manager.reqnext  # Ideally just get this from reqHistoricalData
        key = contract.symbol if barSizeSetting == "5 min" else contract.symbol + barSizeSetting.replace(" ", "")
        if not key in self.__symbols.keys():
            self.__symbols[key] = pd.DataFrame()
        self.__requests[reqId] = (key, False)
        # TODO: NEED TO ASYNC WAIT UNTIL FALSE -> TRUE
        return self.manager.reqHistoricalData(self, reqId, contract, endDateTime, durationStr, barSizeSetting,
                                              whatToShow, useRTH, formatDate, keepUpToDate, chartOptions)

    def receiveHistoricalData(self, reqId, bar):
        '''Put received bar into symbol dictionary'''
        symbol, _ = self.__requests[reqId]
        # if type(bar) is pd.Series:
        #     pass
        # elif type(bar) is pd.DataFrame:
        self.__symbols[symbol] = self.__symbols[symbol].append(bar)

    def receiveHistoricalDataUpdate(self, reqId, bar):
        raise NotImplementedError("receiveHistoricalDataUpdate not implemented")

    def receiveHistoricalDataEnd(self, reqId, start, end):
        self.logger.debug(f"id {reqId} from {start} to {end}")
        symbol, _ = self.__requests[reqId]
        self.__requests[reqId] = (symbol, True)

    def reqHistoricalDataProcessing(self):
        symbol, reqid = zip(*self.__requests.values())
        return not np.any(reqid)

    def placeOrder(self, contract, order):
        reqId = self.manager.reqnext
        self.manager.placeOrder(self, reqId, contract, order)

    def cancelOrder(self, orderId):
        self.manager.cancelOrder(self, orderId)

    @abstractmethod
    def setup(self):
        raise NotImplementedError()

    @abstractmethod
    def openPosition(self, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def closePosition(self, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def closeall(self, *args, **kwargs):
        raise NotImplementedError()
