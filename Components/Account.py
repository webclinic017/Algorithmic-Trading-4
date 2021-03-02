import datetime
from functools import reduce

import pandas as pd

from Services.Datafactory import DataFactory
from Services.MyLogger import MyLogger
from Services.TradingClock import TradingClock
from ibapi.execution import Execution


class Account():
    def __init__(self, startingcapital):
        self.logger = MyLogger.getLogger("ACC")
        self.datafactory = DataFactory.getInstance()
        self.clock = TradingClock.getInstance()
        self.clock.add_callback(self.time_change)
        self.orderLedger = {}
        self.portfolio = {}  # Portfolio(startingcapital)

        self.cash = startingcapital
        self.CASH = pd.Series()
        self.HOLDINGS = pd.Series()

        self.done = False

    @property
    def value(self):
        return self.cash + self.holdings

    @property
    def holdings(self):
        holdings_value = 0
        for symbol, vol in self.portfolio.items():
            holdings_value += self.datafactory.getLatestPrice(symbol, important=False) * vol
        return holdings_value

    @property
    def VALUE(self):
        return self.CASH.add(self.HOLDINGS)


    def stop(self):
        # DODGY
        self.done = True

    def time_change(self):
        if not self.done and self.clock.istrading():
            self.CASH = self.CASH.append(pd.Series(self.cash, index=[self.clock.sync_datetime]))
            self.HOLDINGS = self.HOLDINGS.append(pd.Series(self.holdings, index=[self.clock.sync_datetime]))

    def updatePortfolio(self, contract, execution):
        # key = (contract.symbol, contract.secType)
        key = contract.symbol
        if not key in self.portfolio:
            self.portfolio[key] = 0

        if execution.side == "BOT":
            self.portfolio[key] += execution.shares
            self.cash -= execution.shares * self.datafactory.getLatestPrice(key)
        elif execution.side == "SLD":
            self.portfolio[key] -= execution.shares
            self.cash += execution.shares * self.datafactory.getLatestPrice(key)
        else:
            raise ValueError("No execution side")

    def getPosition(self, symbol):
        def reduceExecutions(ea, eb):
            if eb.side == "BOT":
                qty = ea.cumQty + eb.cumQty
                avg = (ea.cumQty * ea.avgPrice + eb.cumQty * eb.avgPrice) / qty if qty else 0
            else:  #: ea.side == "SLD":
                qty = ea.cumQty - eb.cumQty
                avg = ea.avgPrice

            ec = Execution()
            ec.side = "BOT"
            ec.avgPrice = avg
            ec.cumQty = qty
            return ec

        if symbol in self.portfolio:
            # TODO: avg price
            # filled, price = map(list, zip(*[(o['filled'], o['avgFillPrice']) for id, o in self.orderLedger.items() if o["contract"].symbol == symbol and o["order"].action == "BUY"]))
            netexecution = reduce(reduceExecutions,
                                  [o['execution'] for o in self.orderLedger.values() if o["contract"].symbol == symbol])
            return netexecution.cumQty, netexecution.avgPrice  # self.portfolio[symbol], sum([f * p for f, p in zip(filled, price)])/sum(filled)
        return 0, 0

    def getRealised(self, symbol):
        if symbol in self.portfolio:
            executions = [o['execution'] for o in self.orderLedger.values() if o["contract"].symbol == symbol]
            for i in range(len(executions) - 1, -1, -1):
                if executions[i].side == "BOT":
                    executions = executions[:i]
                else:
                    break

            if len(executions):
                filled, price = map(list, zip(*[(e.cumQty, e.avgPrice) for e in executions if e.side == "BOT"]))
                avg_price = sum([f * p for f, p in zip(filled, price)]) / sum(filled)
                return sum([(execution.avgPrice - avg_price) * execution.cumQty for execution in executions if
                            execution.side == "SLD"])
        return 0

    def winRatioNet(self):
        winners = 0
        losers = 0
        for symbol in self.portfolio:
            try:
                pl = self.getRealised(symbol)
                if pl > 0:
                    winners += 1
                elif pl < 0:
                    losers += 1
            except:
                pass
        return winners, losers

    def winRatio(self):
        # TODO: needs checking
        winners = 0
        losers = 0
        for symbol in self.portfolio:
            try:
                buy_prices = []
                executions = [o['execution'] for o in self.orderLedger.values() if o["contract"].symbol == symbol]
                for execution in executions:
                    if execution.side == "BOT":
                        buy_prices.append(execution.avgPrice)
                    else:
                        for buy_price in buy_prices:
                            if buy_price < execution.avgPrice:
                                winners += 1
                            else:
                                losers += 1
                        buy_prices = []

                # pl = self.getRealised(symbol)
                # if pl > 0:
                #     winners += 1
                # elif pl < 0:
                #     losers += 1
            except:
                pass
        return winners, losers

    def updateOrderLedger(self, **kwargs):
        '''Per order trackign'''
        if "orderId" in kwargs:
            mainkey = kwargs.pop("orderId")
        elif "reqId" in kwargs:
            mainkey = kwargs.pop("reqId")
        else:
            return

        # Add an entry
        if mainkey not in self.orderLedger:
            self.orderLedger[mainkey] = {}

        # Update the order for all kwargs
        for k, v in zip(kwargs.keys(), kwargs.values()):
            self.orderLedger[mainkey][k] = v

        mytime = TradingClock.getInstance().sync_datetime
        self.orderLedger[mainkey]['time'] = mytime - \
                                            datetime.timedelta(minutes=mytime.minute % 5, seconds=mytime.second,
                                                               microseconds=mytime.microsecond)

    def receiveOpenOrder(self, orderId, contract, order, orderState):
        args = locals()
        args.pop("self")
        self.updateOrderLedger(**args)

    def receiveOrderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice,
                           clientId, whyHeld, mktCapPrice):
        args = locals()
        args.pop("self")
        self.updateOrderLedger(**args)

    def receiveExecDetails(self, reqId, contract, execution):
        # args = locals()
        # args.pop("self")
        # self.updateOrderLedger(**args)
        self.updatePortfolio(contract, execution)
        args = locals()
        args.pop("self")
        self.updateOrderLedger(**args)
