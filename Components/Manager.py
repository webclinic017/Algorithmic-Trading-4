from abc import abstractmethod, ABC

from Components.TestApp import TestApp
from Models.Snapshot import Snapshot


class IApiManager(ABC):
    @abstractmethod
    def reqHistoricalData(self, requester, tickerId, contract, endDateTime, durationStr, barSizeSetting, whatToShow,
                          useRTH, formatDate, keepUpToDate, chartOptions):
        raise NotImplementedError()

    @abstractmethod
    def postHistoricalData(self, reqId, bar):
        raise NotImplementedError()

    @abstractmethod
    def postHistoricalDataUpdate(self, reqId, bar):
        raise NotImplementedError()

    @abstractmethod
    def postHistoricalDataEnd(self, reqId, start, end):
        raise NotImplementedError()

    # orders - EClient

    @abstractmethod
    def cancelOrder(self, requester, orderId):
        raise NotImplementedError()

    @abstractmethod
    def placeOrder(self, requester, id, contract, order):
        raise NotImplementedError()

    @abstractmethod
    def postOpenOrder(self, orderId, contract, order, orderState):
        raise NotImplementedError()

    @abstractmethod
    def postOrderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice,
                        clientId,
                        whyHeld, mktCapPrice):
        """
        :param orderId:
        :param status: ApiPending, PendingSubmit, PendingCancel, Submitted, ApiCancelled, Cancelled, Filled, Inactive
        :param filled:
        :param remaining:
        :param avgFillPrice:
        :param permId:
        :param parentId:
        :param lastFillPrice:
        :param clientId:
        :param whyHeld:
        :param mktCapPrice:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    def postExecDetails(self, reqId, contract, execution):
        """When an order is filled either fully or partially, the execDetails and commissionReport events will deliver"""
        raise NotImplementedError()

    # orders - EWrapper

    '''
    @abstractmethod
    def reqAllOpenOrders(self):
        raise NotImplementedError()

    @abstractmethod
    def reqAutoOpenOrders(self, autoBind):
        raise NotImplementedError()

    @abstractmethod
    def reqCompletedOrders(self, apiOnly):
        raise NotImplementedError()

    @abstractmethod
    def reqOpenOrders(self):
        raise NotImplementedError()
    '''

    '''
    @abstractmethod
    def completedOrder(self, contract, order, orderState):
        raise NotImplementedError()

    @abstractmethod
    def completedOrdersEnd(self):
        raise NotImplementedError
    '''

    '''
    @abstractmethod
    def openOrderEnd(self):
        raise NotImplementedError()

    @abstractmethod
    def orderBound(self,orderId, apiClientId, apiOrderId):
        raise NotImplementedError()
    '''


class Manager(IApiManager):
    _reqnext = 1

    def __init__(self, account=None, simtracker=None):
        self.done = False
        self.account = account
        self.request_book = {}
        self.order_book = {}
        self.positions = {}

        self.app = TestApp(self)
        self.simtracker = simtracker

    @property
    def reqnext(self):
        global global_order_counter
        if not ('global_order_counter' in globals()):
            global_order_counter = 0
        global_order_counter += 1
        return global_order_counter

    def stop(self):
        # DODGY
        self.done = True

    def reqHistoricalData(self, requester, tickerId, contract, endDateTime, durationStr, barSizeSetting, whatToShow,
                          useRTH, formatDate, keepUpToDate, chartOptions):
        """Make a request on behalf of requester"""
        self.request_book[tickerId] = requester
        self.app.reqHistoricalData(tickerId, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH,
                                   formatDate, keepUpToDate, chartOptions)

    def postHistoricalData(self, reqId, bar):
        """Post result to mapped requester"""
        self.request_book[reqId].receiveHistoricalData(reqId, bar)

    def postHistoricalDataUpdate(self, reqId, bar):
        """Post result to mapped requester"""
        self.request_book[reqId].receiveHistoricalDataUpdate(reqId, bar)

    def postHistoricalDataEnd(self, reqId, start, end):
        """Post result to mapped requester"""
        self.request_book[reqId].receiveHistoricalDataEnd(reqId, start, end)

    def placeOrder(self, requester, id, contract, order):
        datakey = contract.symbol+requester.mainBarsize.replace(" ", "")
        snapshot = Snapshot(requester.name, requester[datakey], requester.indicators.copy(), contract, order)
        if self.simtracker is not None:
            self.simtracker.add_shapshot(snapshot)
        self.app.placeOrder(id, contract, order)

    def cancelOrder(self, requester, orderId):
        self.app.cancelOrder(orderId)

    def postOpenOrder(self, orderId, contract, order, orderState):
        if self.account is not None:
            self.account.receiveOpenOrder(orderId, contract, order, orderState)

    def postOrderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice,
                        clientId, whyHeld, mktCapPrice):
        if self.account is not None:
            self.account.receiveOrderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId,
                                            lastFillPrice,
                                            clientId, whyHeld, mktCapPrice)

    def postExecDetails(self, reqId, contract, execution):
        if self.account is not None:
            self.account.receiveExecDetails(reqId, contract, execution)
