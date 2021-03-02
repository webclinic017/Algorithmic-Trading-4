import datetime
import sched
import smtplib
import time
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz

from Components.Account import Account
from Components.Manager import Manager
from DataScrape.ScrapeReddit import ASX_LISTING
from Services.Datafactory import DataFactory
from Services.MyLogger import MyLogger
from Services.SimTracker import SimTracker
from Services.SimViewer import StrategyView
from Services.TradingClock import TradingClock
from Strategies.Crystal import CrystalV3
from Strategies.RocketCatcher import RocketCatcher
from _config import TICKERS_LEDGER
from _devconfig import *

import random
import pandas as pd

def generate_message(simtracker):
    # TODO: Make one big email
    # https://stackoverflow.com/questions/920910/sending-multipart-html-emails-which-contain-embedded-images

    # The mail addresses and password
    sender_address = MY_EMAIL
    sender_pass = MY_EMAIL_PASS

    # Setup the MIME
    message = MIMEMultipart('related')
    message_alt = MIMEMultipart('alternative')
    message.attach(message_alt)


    message_text = ""
    while len(simtracker.snapshots):
        snapshot = simtracker.snapshots.pop(0)

        symbol = snapshot.contract.symbol
        action = snapshot.order.action
        file = f"C:/Users/liamd/Documents/Project/AlgoTrading/Output/Emails/{symbol}_{action}_{clock.sync_datetime.strftime('%m%d%h')}.png"
        fig, ax, leg_indicators = StrategyView.snapshot_to_fig(snapshot, account, savefile=file)


        # We reference the image in the IMG SRC attribute by the ID we give it below
        message_text += f'<p>SYMBOL: {symbol},  ACTION: {action},  DATE:{snapshot.data.index[-1]} </p>' + \
                        f'<br><img src="cid:image_{symbol}">' + \
                        f'<br>' + \
                        "<p>"+", ".join([k + ": " + v for k, v in leg_indicators.items()]) + "</p>" +\
                        f'<br>'


        # This example assumes the image is in the current directoryddd
        fp = open(file, 'rb')
        msg_image = MIMEImage(fp.read())
        fp.close()


        # Define the image's ID as referenced above
        msg_image.add_header('Content-ID', f'<image_{symbol}>')
        message.attach(msg_image)

    msg_text = MIMEText(message_text, 'html')
    message_alt.attach(msg_text)

    message['From'] = sender_address
    message['Subject'] = 'Stocks only go up'
    message.preamble = 'This is a multi-part message in MIME format.'

    # Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls()
    session.login(sender_address, sender_pass)
    for receiver_address in EMAIL_LIST:
        message['To'] = receiver_address
        session.sendmail(sender_address, receiver_address, message.as_string())
    session.quit()





if __name__ == "__main__":

    MyLogger.configure(20)
    logger = MyLogger.getLogger("MAIN")

    # services
    DataFactory.repaired = True
    DataFactory.live_data = True
    clock, datafactory = TradingClock.getInstance(), DataFactory.getInstance()


    # absolute times to check for an update
    times = [
        datetime.time(9, 30),
        datetime.time(10, 30),
        datetime.time(11, 30),
        datetime.time(12, 30),
        datetime.time(13, 30),
        datetime.time(14, 30),
        datetime.time(15, 30),
        datetime.time(16, 30)
    ]
    dates = [clock.mytz.localize(datetime.datetime.combine(datetime.date.today(), time)) for time in times]
    clock.sync_datetime = dates.pop(0)

    # Components
    account = Account(100000)
    simtracker = SimTracker()
    manager = Manager(account, simtracker)
    strategy = CrystalV3(manager, "C3", ["VAS"], {
        "days_required": 31,
        "ma_days": 1,
        "buy_volume_sigma": 0.5,
        "sell_volume_sigma": 0.5,
        "ma_long_days": 3,
        "positive_sigma": 0.35,
        "negative_sigma": 0.3
    })  # not optimised

    tickers_ledger = pd.read_csv(TICKERS_LEDGER)
    asx_listings = pd.read_csv(ASX_LISTING)

    symbols = random.choices(
        [s for t, s, mc, l in zip(
            asx_listings.title.values,
            asx_listings.code.values,
            asx_listings.market_cap.values,
            asx_listings.low.values)
         if
         (0.01 < l < 5) and
         (s + ".AX" in tickers_ledger.TICKER.values) and
         (t.find("Ltd") > 0)], k=5)

    strategy_two = RocketCatcher(manager, "RC", symbols, {
            "days_required_5m": 3,
            "days_required_1d": 31,
            "from_max_limit": 20,
            "from_min_limit": 15,
            "volume_sigma": 0.25,
            "pumps": 5
        })

    # PREPROCESSING -
    # 1. Data scrape / validate

    s = sched.scheduler(time.time, time.sleep)

    def run_update():
        # do your stuff
        clock.sync_datetime = dates.pop(0)

        logger.info(f"Running update... {datetime.datetime.now()}")

        try:
            strategy.update()
        except Exception as e:
            logger.exception(e)

        try:
            strategy_two.update()
        except Exception as e:
            logger.exception(e)

        if len(simtracker.snapshots):
            generate_message(simtracker)

        if not len(dates):
            return

        next = dates[0].astimezone(pytz.timezone('Australia/Brisbane'))
        s.enterabs(time.mktime(next.timetuple()), 1, run_update)
        # s.enter(1, 1, run_update)


    next = dates[0].astimezone(pytz.timezone('Australia/Brisbane'))
    s.enterabs(time.mktime(next.timetuple()), 1, run_update)
    # s.enter(1, 1, run_update)
    s.run()
