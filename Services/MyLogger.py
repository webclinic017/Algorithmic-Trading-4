import logging

from Services.TradingClock import TradingClock


class MyLogger(logging.Logger):
    # https://stackoverflow.com/questions/47888855/python3-add-logging-level/47912062
    # https://stackoverflow.com/questions/11232230/logging-to-two-files-with-different-settings
    # https://stackoverflow.com/questions/4441842/python-logging-configuration-file

    __DEFAULT_FORMAT = "%(simtime)s| %(levelname)s (%(name)s):  %(message)s"
    __TRADE_NAME, TRADE = "TRADE", 25
    __OPTY_NAME, OPTY = "OPTIMISATION", 35
    configured = False

    def __init__(self, *args, **kwargs):
        logging.addLevelName(self.__TRADE_NAME, self.TRADE)
        logging.addLevelName(self.__OPTY_NAME, self.OPTY)

        super().__init__(*args, **kwargs)

    def trade(self, contract, execution, *args, **kwargs):

        msg = f"{contract.symbol} {execution.side} avg: ${execution.avgPrice:0.3f} vol: {execution.cumQty}"
        if self.isEnabledFor(self.TRADE):
            self._log(self.TRADE, msg, args, **kwargs)

    def optimisation(self, msg, *args, **kwargs):
        if self.isEnabledFor(self.OPTY):
            self._log(self.OPTY, msg, args, **kwargs)

    @staticmethod
    def configure(level=20):
        MyLogger.configured = True
        logging.setLoggerClass(MyLogger)
        logging.basicConfig(
            level=level,
            format=MyLogger.__DEFAULT_FORMAT
        )

    @staticmethod
    def getLogger(name, file=None, level=None):
        if not MyLogger.configured:
            MyLogger.configure()

        # TODO: file writeout cleanup
        # old version

        logger = logging.getLogger(name)
        if file != None:
            handler1 = logging.FileHandler("C:/Users/liamd/Documents/Project/AlgoTrading/Output/" + file)
            formatter = logging.Formatter(MyLogger.__DEFAULT_FORMAT)
            handler1.setFormatter(formatter)
            if level is None:
                level = MyLogger.TRADE
            handler1.setLevel(level)
            filter = MyFilter(level)
            handler1.addFilter(filter)
            logger.addHandler(handler1)

        logger.addFilter(AppFilter())
        return logger


class AppFilter(logging.Filter):
    def filter(self, record):
        record.simtime = TradingClock.getInstance().sync_datetime
        return True


class MyFilter(object):
    def __init__(self, level):
        self.__level = level

    def filter(self, record):
        record.simtime = TradingClock.getInstance().sync_datetime
        return record.levelno <= self.__level


if __name__ == "__main__":
    logger = MyLogger.getLogger('A', file="optimiser.log", level=MyLogger.OPTY)
    logger.optimisation("Bought")
    logger.info("X")

    # logger.sell('This seems to work')
    # def setup_logger(name, log_file=None, level=None):
    #     """To setup as many loggers as you want"""
    #     logger = logging.getLogger(name)
    #     if log_file:
    #         handler = logging.FileHandler(log_file)
    #         handler.setFormatter(formatter)
    #         logger.addHandler(handler)
    #     if level:
    #         logger.setLevel(level)
    #     return logger
