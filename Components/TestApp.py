import datetime

import pandas as pd

from Services.Datafactory import DataFactory
from Services.MyLogger import MyLogger
from Services.TradingCalendar import TradingCalendar
from Services.TradingClock import TradingClock
from ibapi.execution import Execution
from ibapi.order_state import OrderState


class TestApp():

    def __init__(self, endpoint):
        self.logger = MyLogger.getLogger('TestApp', file='trades.log', level=MyLogger.TRADE)
        self.clock = TradingClock.getInstance()
        self.datafactory = DataFactory.getInstance()

        self.endpoint = endpoint
        self.clock.add_callback(self.time_change)
        self.pending_orders = {}
        self.historical_subscribers = {}

    def startup(self):
        # https: // interactivebrokers.github.io / tws - api / connection.html
        pass

    def teardown(self):
        pass

    def error(self):
        pass

    def time_change(self):
        # todo: fix fix fix - del
        if not self.endpoint.done:
            self.reqHistoricalDataSubscribers()

    def reqMarketData(self, tickerId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions):
        """Requests real time market data. Returns market data for an instrument either in real time or 10-15 minutes delayed
        :param tickerId: the request's identifier
        :param contract: the Contract for which the data is being requested
        :param genericTickList: comma separated ids of the available generic ticks: ...
        :param snapshot: for users with corresponding real time market data subscriptions. A true value will return a one-time snapshot, while a false value will provide streaming data.
        :param regulatorySnapshot: snapshot for US stocks requests NBBO snapshots for users which have "US Securities Snapshot Bundle" subscription but not corresponding Network A, B, or C subscription necessary for streaming * market data. One-time snapshot of current market price that will incur a fee of 1 cent to the account per snapshot.
        :param mktDataOptions:
        :return: None
        """
        pass

    def tickPrice(self, tickerId, field, price, attribs):
        '''Market data tick price callback. Handles all price related ticks. Every tickPrice callback is followed by a tickSize.
        A tickPrice value of -1 or 0 followed by a tickSize of 0 indicates there is no data for this field currently available, whereas a tickPrice with a positive tickSize indicates an active quote of 0 (typically for a combo contract).
        :param tickerId: the request's unique identifier.
        :param field: the type of the price being received (i.e. ask price)
        :param price: the actual price.
        :param attribs: an TickAttrib object that contains price attributes such as TickAttrib::CanAutoExecute, TickAttrib::PastLimit and TickAttrib::PreOpen.
        :return:
        '''
        pass

    def tickSize(self, tickerId, field, size):
        '''Market data tick size callback. Handles all size-related ticks.
        :param tickerId: the request's unique identifier.
        :param field: the type of size being received (i.e. bid size)
        :param size: the actual size. US stocks have a multiplier of 100.
        :return:
        '''
        pass

    def parseHistoricalDataArgs(self, tickerId, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH,
                                formatDate, keepUpToDate, chartOptions):
        if formatDate == 0:
            raise NotImplementedError(f"formatDate value {formatDate} not supported; use 1:yyyyMMdd HH:mm:ss")
        elif formatDate == 1:
            dateformat = "%Y%m%d %H:%M:%S"
        else:
            raise ValueError(f"Format date value {formatDate} not recognised must be 0:sys or 1:yyyyMMdd HH:mm:ss")

        # End time
        currtime = self.clock.sync_datetime
        if endDateTime == "":
            endtime = currtime
        else:
            endtime = datetime.strptime(endDateTime, dateformat)
            if currtime < endtime:
                raise ValueError(f"End time {endtime} cannot be greater than current time {currtime}")

        # TODO: Public holidays in lookback

        # Start time
        lookback_val = int(durationStr.split(" ")[0])
        lookback_unit = durationStr.split(" ")[-1]
        if lookback_unit == "S":
            starttime = endtime - datetime.timedelta(seconds=lookback_val)
        elif lookback_unit == "D":
            starttime = TradingCalendar.add_trading_days(endtime, -lookback_val)
        elif lookback_unit == "W":
            starttime = endtime - datetime.timedelta(days=lookback_val * 7)
        elif lookback_unit == "M":
            lb_month = endtime.month - lookback_val % 12
            lb_year = endtime.year - lookback_val // 12
            starttime = datetime.datetime(
                year=lb_year if lb_month >= 1 else lb_year - 1, month=lb_month if lb_month >= 1 else lb_month + 12,
                day=endtime.day, hour=endtime.hour, minute=endtime.minute, second=endtime.second)
        elif lookback_unit == "Y":
            starttime = datetime.datetime(
                year=endtime.year - lookback_val, month=endtime.month,
                day=endtime.day, hour=endtime.hour, minute=endtime.minute, second=endtime.second)
        else:
            raise ValueError(f"Invalid durationStr argument {durationStr}, unit {lookback_unit} not recognised")

        return starttime, endtime, dateformat

    def reqHistoricalData(self, tickerId, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH,
                          formatDate, keepUpToDate, chartOptions):
        """ Requests contracts' historical data. When requesting historical data, a finishing time and date is required along with a duration string.
        The resulting bars will be returned in EWrapper::historicalData
        :param tickerId: the request's unique identifier.
        :param contract: the contract for which we want to retrieve the data.
        :param endDateTime: request's ending time with format yyyyMMdd HH:mm:ss {TMZ}
        :param durationStr: the amount of time for which the data needs to be retrieved: ...
        :param barSizeSetting: the size of the bar: ...
        :param whatToShow: the kind of information being retrieved: ...
        :param useRTH: set to 0 to obtain the data which was also generated outside of the Regular Trading Hours, set to 1 to obtain only the RTH data
        :param formatDate: set to 1 to obtain the bars' time as yyyyMMdd HH:mm:ss, set to 2 to obtain it like system time format in seconds
        :param keepUpToDate: 	set to True to received continuous updates on most recent bar data. If True, and endDateTime cannot be specified.
        :param chartOptions:
        :return:
        """
        if whatToShow != "BID_ASK":
            raise NotImplementedError(f"whatToShow {whatToShow} not supported; use \"BID_ASK\"")

        data = self.datafactory.loadSymbol(contract.symbol, barsize=barSizeSetting)
        start, end, dateformat = self.parseHistoricalDataArgs(tickerId, contract, endDateTime, durationStr,
                                                              barSizeSetting, whatToShow, useRTH, formatDate,
                                                              keepUpToDate, chartOptions)

        #tosend = data.loc[start:end]
        tosend = data[(start <= data.index) & (data.index <= end)]
        # try:
        #     period = min([abs(d1 - d2) for d1, d2 in zip(data.index[1:], data.index[:-1])])
        #     if period > datetime.timedelta(minutes=5):
        #         latest = data.index[-1]
        #         if period == datetime.timedelta(days=1):
        #             if latest.date() != TradingClock.getInstance().date:
        #                 data5 = self.datafactory.loadSymbol(contract.symbol, barsize="5 min")
        #                 data5 = data5[(pd.Series(data5.index).transform(lambda x: x.date()) == latest.date()).values]
        #                 tosend = pd.concat([tosend, pd.DataFrame(
        #                     {
        #                         "Open": data5.Open.iloc[0],
        #                         "High": max(data5.High),
        #                         "Low": min(data5.Low),
        #                         "Close": data5.Close.iloc[-1],
        #                         "Adj Close": data5.AdjClose.iloc[-1],
        #                         "Volume": sum(data5.Volume.values)
        #                     }, index = [TradingClock.getInstance().sync_datetime]
        #                 )])
        # except Exception as e:
        #     pass

        iterrows_rows = max(1, len(tosend.index) - 1)

        # Send a heap at once
        self.historicalData(tickerId, tosend.iloc[:iterrows_rows])
        row = None

        # Send some rows, as should normally happen
        for i, row in tosend.iloc[iterrows_rows:].iterrows():
            self.historicalData(tickerId, row)
        self.historicalDataEnd(tickerId, start.strftime(dateformat), end.strftime(dateformat))

        lastdate = row.name if row is not None else self.clock.sync_datetime

        if keepUpToDate:
            self.historical_subscribers[tickerId] = (
                contract, barSizeSetting, whatToShow, useRTH, formatDate, chartOptions, lastdate)

    def reqHistoricalDataSubscribers(self):
        self.logger.debug("req historicaldata subscribers called")
        for tickerId, (contract, barSizeSetting, whatToShow, useRTH, formatDate, chartOptions, lastindex) in zip(
                self.historical_subscribers.keys(), self.historical_subscribers.values()):

            self.logger.debug(f"req historicaldata subscribers called for {tickerId}")

            data = self.datafactory.loadSymbol(contract.symbol, barsize=barSizeSetting)
            from_date = lastindex
            to_date = pd.to_datetime(self.clock.sync_datetime).tz_convert(from_date.tzinfo)
            #undelivered = data[from_date:to_date].iloc[1:]
            undelivered = data[(from_date < data.index) & (data.index <= to_date)]#.iloc[1:]


            # Send the data, update dict
            if not undelivered.empty:
                self.logger.debug(f"req historicaldata subscribers called for {tickerId} with undelivered rows")
                for i, row in undelivered.iterrows():
                    self.historicalData(tickerId, row)
                self.historical_subscribers[tickerId] = (
                    contract, barSizeSetting, whatToShow, useRTH, formatDate, chartOptions, row.name)

    def historicalData(self, reqId, bar):
        '''Returns the requested historical data bars
        :param reqId: the request's identifier
        :param bar: the OHLC historical data Bar. The time zone of the bar is the time zone chosen on the TWS login screen. Smallest bar size is 1 second.
        :return:
        '''
        # print("HistoricalData. ", reqId, " Date:", bar.index, "Open:", bar.Open, "High:", bar.High, "Low:", bar.Low, "Close:", bar.Close, "Volume:", bar.Volume)
        self.endpoint.postHistoricalData(reqId, bar)

    def historicalDataUpdate(self, reqId, bar):
        """Think this is only called when replacing a bar"""
        self.endpoint.postHistoricalDataUpdate(reqId, bar)

    def historicalDataEnd(self, reqId, start, end):
        self.endpoint.postHistoricalDataEnd(reqId, start, end)

    def placeOrder(self, orderId, contract, order):
        if order.orderType != "MKT":
            raise NotImplementedError(f"MKT order is only supported type, {order.orderType} fail")

        # TODO: need an exchange class
        # TODO: slippageeeeee

        volume = order.totalQuantity
        price = self.datafactory.getLatestPrice(contract.symbol)

        # OPENED
        orderState = OrderState()
        orderState.status = "Submitted"
        self.openOrder(orderId, contract, order, orderState)
        self.orderStatus(orderId, "Submitted", 0, volume, 0, -1, -1, 0, -1, "", -1)

        # EXECUTE
        execution = Execution()
        execution.orderId = orderId
        execution.clientId = -1
        execution.execId = "-1"
        execution.Time = f"{self.clock.sync_datetime.time().hour:02d}{self.clock.sync_datetime.time().hour:02d}"
        execution.side = "BOT" if order.action == "BUY" else "SLD"
        execution.shares = volume
        execution.price = price
        execution.cumQty = volume
        execution.avgPrice = price
        self.execDetails(orderId, contract, execution)

        # FILLEd
        orderState.status = "Filled"
        self.openOrder(orderId, contract, order, orderState)
        self.orderStatus(orderId, "Filled", volume, 0, price, -1, -1, price, -1, "", -1)

    def cancelOrder(self, orderId):
        raise NotImplementedError("Cancel not implemented. Stocks only go up ~~")

    def openOrder(self, orderId, contract, order, orderState):
        self.endpoint.postOpenOrder(orderId, contract, order, orderState)

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice,
                    clientId, whyHeld, mktCapPrice):
        self.endpoint.postOrderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice,
                                      clientId, whyHeld, mktCapPrice)

    def execDetails(self, reqId, contract, execution):
        self.logger.trade(contract, execution)
        self.endpoint.postExecDetails(reqId, contract, execution)
